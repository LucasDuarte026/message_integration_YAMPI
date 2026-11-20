import smtplib
import logging
import time
import threading
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Any, Dict, List, Optional
import re
import os
import mimetypes
import uuid
from src.domain.interfaces import MessageProviderProtocol
from src.core.macros import (
    MACRO_SMTP_THROTTLE_DELAY_SEG,
    MACRO_SMTP_MAX_RETRIES,
    MACRO_SMTP_RETRY_BACKOFF_SEG,
    MACRO_SMTP_TIMEOUT_SEG,
    MACRO_DEFAULT_FALLBACK_FROM_EMAIL,
    MACRO_EMAIL_MASK_VISIBLE_PREFIX_CHARS,
    MACRO_EMAIL_FROM_NAME,
    MACRO_EMAIL_REPLY_TO,
    MACRO_EMAIL_MESSAGE_ID_DOMAIN,
    MACRO_EMAIL_UNSUBSCRIBE_URL,
    MACRO_EMAIL_UNSUBSCRIBE_MAILTO,
    MACRO_DEFAULT_EMAIL_ASSETS_DIR,
)
from src.core.telemetry import (
    add_smtp_retry_breadcrumb,
    capture_email_dispatch_error,
    extract_recipient_domain,
    extract_smtp_error_details,
    record_email_dispatch_failed,
    record_email_dispatch_sent,
    record_email_dispatch_started,
    sanitize_error_message,
    start_smtp_span,
)

logger = logging.getLogger(__name__)

class SMTPEmailProvider(MessageProviderProtocol):
    """
    Adaptador concreto para envio de E-mail utilizando o protocolo SMTP.
    Suporta conexão segura via SSL ou TLS (portas 465/587), construção MIME moderna
    via EmailMessage (RFC 2046/5322/8058), conexão persistente (Stateful/Pooling) com
    Lock (Throttling) e mecanismo de Retry com Exponential Backoff.
    """
    def __init__(
        self,
        host: str,
        port: int,
        user: Optional[str],
        password: Optional[str],
        from_addr: Optional[str],
        from_name: str = MACRO_EMAIL_FROM_NAME,
        reply_to: Optional[str] = MACRO_EMAIL_REPLY_TO,
        message_id_domain: str = MACRO_EMAIL_MESSAGE_ID_DOMAIN,
        unsubscribe_url: Optional[str] = MACRO_EMAIL_UNSUBSCRIBE_URL,
        unsubscribe_mailto: Optional[str] = MACRO_EMAIL_UNSUBSCRIBE_MAILTO,
        assets_dir: Optional[str] = MACRO_DEFAULT_EMAIL_ASSETS_DIR,
        promo_user: Optional[str] = None,
        promo_password: Optional[str] = None,
        promo_from_addr: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr or user or MACRO_DEFAULT_FALLBACK_FROM_EMAIL
        self.from_name = from_name
        self.reply_to = reply_to
        self.message_id_domain = message_id_domain
        self.unsubscribe_url = unsubscribe_url
        self.unsubscribe_mailto = unsubscribe_mailto
        self.assets_dir = assets_dir or MACRO_DEFAULT_EMAIL_ASSETS_DIR
        self.promo_user = promo_user
        self.promo_password = promo_password
        self.promo_from_addr = promo_from_addr or promo_user or self.from_addr
        
        self._lock = threading.Lock()
        self._server = None
        self._promo_server = None

    def _close_server_attr(self, attr_name: str) -> None:
        server = getattr(self, attr_name, None)
        if server is not None:
            try:
                server.quit()
            except Exception:
                try:
                    server.close()
                except Exception:
                    pass
            finally:
                setattr(self, attr_name, None)

    def close(self) -> None:
        """Encerra de forma segura as conexões SMTP persistentes ao final do ciclo."""
        with self._lock:
            self._close_server_attr("_server")
            self._close_server_attr("_promo_server")

    def _connect(self, server_attr: str = "_server", user: Optional[str] = None, password: Optional[str] = None) -> None:
        """
        Garante que o cliente SMTP para a conta informada está conectado e logado.
        Não é thread-safe por si só; deve ser chamado de dentro do self._lock.
        """
        resolved_user = self.user if user is None else user
        resolved_password = self.password if password is None else password
        server = getattr(self, server_attr, None)

        if server is not None:
            try:
                status = server.noop()[0]
                if status == 250:
                    return
            except smtplib.SMTPServerDisconnected:
                server = None
                setattr(self, server_attr, None)
            except Exception as e:
                logger.warning(f"[SMTP] Erro inesperado ao verificar conexão viva (noop): {e}")
                server = None
                setattr(self, server_attr, None)

        if server is None:
            if self.port == 465:
                logger.info(f"Estabelecendo nova conexão SMTP segura (SSL) com {self.host}:{self.port}...")
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=MACRO_SMTP_TIMEOUT_SEG)
            else:
                logger.info(f"Estabelecendo nova conexão SMTP (STARTTLS) com {self.host}:{self.port}...")
                server = smtplib.SMTP(self.host, self.port, timeout=MACRO_SMTP_TIMEOUT_SEG)
                server.starttls()
            
            if resolved_user and resolved_password:
                logger.info(f"Autenticando usuário SMTP '{resolved_user}'...")
                server.login(resolved_user, resolved_password)
            setattr(self, server_attr, server)

    def _mask_email(self, email: str) -> str:
        if not email or '@' not in email:
            return "***@***"
        parts = email.split('@', 1)
        user_part, domain_part = parts[0], parts[1]
        
        prefix_len = MACRO_EMAIL_MASK_VISIBLE_PREFIX_CHARS
        if len(user_part) > (prefix_len + 1):
            first_chars = user_part[:prefix_len]
            last_char = user_part[-1]
            stars = '*' * (len(user_part) - (prefix_len + 1))
            return f"{first_chars}{stars}{last_char}@{domain_part}"
        elif len(user_part) > 2:
            first_char = user_part[0]
            last_char = user_part[-1]
            stars = '*' * (len(user_part) - 2)
            return f"{first_char}{stars}{last_char}@{domain_part}"
        else:
            return f"{'*' * len(user_part)}@{domain_part}"

    def _format_from_header(self, sender_addr: Optional[str] = None) -> str:
        """Formata o cabeçalho From com nome amigável caso ainda não esteja formatado."""
        addr = sender_addr or self.from_addr
        if self.from_name and "<" not in addr:
            return formataddr((self.from_name, addr))
        return addr

    def _resolve_local_asset_path(self, raw_url: str, project_root: str) -> str:
        """
        Resolve o caminho de uma imagem local considerando o diretório modular `assets_dir`.
        Permite externalizar as imagens fora do repositório Git (ex.: `/app/email_assets`).
        """
        if raw_url.startswith("file://"):
            return raw_url.replace("file://", "", 1)
        if raw_url.startswith("/"):
            return raw_url

        default_prefix = f"{MACRO_DEFAULT_EMAIL_ASSETS_DIR.rstrip('/')}/"
        base_assets_dir = (
            self.assets_dir
            if os.path.isabs(self.assets_dir)
            else os.path.join(project_root, self.assets_dir)
        )

        if raw_url.startswith(default_prefix):
            rel_subpath = raw_url[len(default_prefix):]
            return os.path.join(base_assets_dir, rel_subpath)

        candidate = os.path.join(base_assets_dir, raw_url)
        if os.path.exists(candidate):
            return candidate
        return os.path.join(project_root, raw_url)

    def _fallback_plain_text(self, html_body: str) -> str:
        """Fallback mínimo de texto puro caso plain_text não seja fornecido pelo chamador."""
        without_blocks = re.sub(r"(?is)<(style|script|head).*?>.*?</\1>", " ", html_body)
        without_tags = re.sub(r"<[^>]+>", " ", without_blocks)
        return re.sub(r"\s+", " ", without_tags).strip() or "Visualize este e-mail em um cliente compatível com HTML."

    def _record_smtp_retry_failure(
        self,
        exc: BaseException,
        *,
        attempt: int,
        channel: str,
        recipient_domain: str,
        raw_email: str,
        masked_email: str,
        retry_history: List[Dict[str, Any]],
    ) -> str:
        """Registra metadados sanitizados e breadcrumb de uma tentativa SMTP falha."""
        sanitized_err = sanitize_error_message(
            str(exc), raw_email=raw_email, masked_email=masked_email
        )
        smtp_details = extract_smtp_error_details(
            exc, raw_email=raw_email, masked_email=masked_email
        )
        retry_history.append(
            {
                "attempt": attempt,
                "error_type": type(exc).__name__,
                "message": sanitized_err,
                **smtp_details,
            }
        )
        add_smtp_retry_breadcrumb(
            attempt=attempt,
            max_retries=MACRO_SMTP_MAX_RETRIES,
            error_type=type(exc).__name__,
            smtp_code=smtp_details.get("smtp_code"),
            channel=channel,
            recipient_domain=recipient_domain,
        )
        return sanitized_err

    def send_email_message(
        self,
        email: str,
        subject: str,
        html_body: str,
        plain_text: Optional[str] = None,
        is_promotional: bool = False,
    ) -> bool:
        masked_email = self._mask_email(email)
        channel = "promotional" if is_promotional else "transactional"
        recipient_domain = extract_recipient_domain(email)
        base_metric_attrs: Dict[str, Any] = {
            "email.provider": "smtp",
            "email.channel": channel,
            "email.recipient_domain": recipient_domain,
            "smtp.host": self.host,
            "smtp.port": self.port,
        }
        record_email_dispatch_started(base_metric_attrs)

        try:
            use_promo_account = bool(is_promotional and self.promo_user and self.promo_password)
            account_slot = "promo" if use_promo_account else "primary"
            active_server_attr = "_promo_server" if use_promo_account else "_server"
            active_user = self.promo_user if use_promo_account else self.user
            active_password = self.promo_password if use_promo_account else self.password
            active_from_addr = self.promo_from_addr if use_promo_account else self.from_addr

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self._format_from_header(active_from_addr)
            msg["To"] = email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain=self.message_id_domain)
            if self.reply_to:
                msg["Reply-To"] = self.reply_to

            if is_promotional:
                unsubscribe_entries = []
                if self.unsubscribe_url:
                    unsubscribe_entries.append(f"<{self.unsubscribe_url}>")
                if self.unsubscribe_mailto:
                    unsubscribe_entries.append(f"<{self.unsubscribe_mailto}>")
                if unsubscribe_entries:
                    msg["List-Unsubscribe"] = ", ".join(unsubscribe_entries)
                    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

            # Parse HTML for local files (somente quando não forem URLs HTTPS/CDN externas)
            images_to_attach = []
            html_processed = html_body
            
            pattern = r'(?:src|background)=["\'](?!http|https|cid:|data:|mailto:)([^"\']+)["\']'
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            
            for match in re.finditer(pattern, html_body):
                full_url = match.group(1)
                filepath = self._resolve_local_asset_path(full_url, project_root)
                
                if not os.path.exists(filepath):
                    logger.warning(f"Imagem local não encontrada para anexar: {filepath}")
                    continue
                
                cid = f"img_{uuid.uuid4().hex[:8]}"
                html_processed = html_processed.replace(f'"{full_url}"', f'"cid:{cid}"').replace(f"'{full_url}'", f"'cid:{cid}'")
                images_to_attach.append((cid, filepath))

            # 1. Parte text/plain obrigatória antes do text/html (RFC 2046)
            resolved_plain_text = plain_text.strip() if isinstance(plain_text, str) and plain_text.strip() else self._fallback_plain_text(html_processed)
            msg.set_content(resolved_plain_text, subtype="plain", charset="utf-8")

            # 2. Parte text/html como alternativa de maior fidelidade
            msg.add_alternative(html_processed, subtype="html", charset="utf-8")

            # 3. Anexa eventuais imagens locais (ex.: *_q75.webp) como related na parte HTML
            if images_to_attach:
                html_part = msg.get_payload()[1]
                for cid, filepath in images_to_attach:
                    try:
                        with open(filepath, 'rb') as f:
                            img_data = f.read()
                        
                        if filepath.lower().endswith('.webp'):
                            subtype = 'webp'
                        else:
                            mime_guess, _ = mimetypes.guess_type(filepath)
                            subtype = mime_guess.split('/')[1] if mime_guess and '/' in mime_guess else 'jpeg'
                        
                        html_part.add_related(
                            img_data,
                            maintype='image',
                            subtype=subtype,
                            cid=f'<{cid}>',
                            disposition='inline',
                        )
                    except Exception as e:
                        logger.warning(f"Erro ao anexar imagem inline ({filepath}): {e}")
            
            with self._lock:
                last_exc: Optional[BaseException] = None
                retry_history: List[Dict[str, Any]] = []
                for attempt in range(1, MACRO_SMTP_MAX_RETRIES + 1):
                    try:
                        with start_smtp_span(
                            f"SMTP sendmail ({channel})",
                            data={
                                "smtp.host": self.host,
                                "smtp.port": self.port,
                                "smtp.attempt": attempt,
                                "smtp.account_slot": account_slot,
                                "email.channel": channel,
                            },
                        ):
                            self._connect(active_server_attr, active_user, active_password)

                            logger.info(f"Despachando mensagem SMTP para {masked_email}...")
                            refused = getattr(self, active_server_attr).sendmail(
                                active_from_addr, [email], msg.as_string()
                            )
                            if isinstance(refused, dict) and refused:
                                raise smtplib.SMTPRecipientsRefused(
                                    {self._mask_email(addr): err for addr, err in refused.items()}
                                )

                        # Ping de sucesso imediatamente após confirmação do sendmail e antes do throttling
                        record_email_dispatch_sent(
                            {
                                **base_metric_attrs,
                                "smtp.attempts": attempt,
                                "smtp.account_slot": account_slot,
                            }
                        )

                        logger.info(f"E-mail enviado com sucesso via SMTP para: {masked_email}")

                        # Throttle/Rate Limit
                        time.sleep(MACRO_SMTP_THROTTLE_DELAY_SEG)
                        return True

                    except smtplib.SMTPServerDisconnected as e:
                        last_exc = e
                        sanitized_err = self._record_smtp_retry_failure(
                            e,
                            attempt=attempt,
                            channel=channel,
                            recipient_domain=recipient_domain,
                            raw_email=email,
                            masked_email=masked_email,
                            retry_history=retry_history,
                        )
                        logger.warning(
                            f"[SMTP] Conexão caiu na tentativa {attempt}/{MACRO_SMTP_MAX_RETRIES}: {sanitized_err}"
                        )
                        setattr(self, active_server_attr, None)
                    except (smtplib.SMTPException, OSError, TimeoutError) as e:
                        last_exc = e
                        sanitized_err = self._record_smtp_retry_failure(
                            e,
                            attempt=attempt,
                            channel=channel,
                            recipient_domain=recipient_domain,
                            raw_email=email,
                            masked_email=masked_email,
                            retry_history=retry_history,
                        )
                        logger.warning(
                            f"[SMTP] Erro transitório na tentativa {attempt}/{MACRO_SMTP_MAX_RETRIES} para {masked_email}: {sanitized_err}"
                        )
                        setattr(self, active_server_attr, None)

                    # Se não for a última tentativa, aplica o backoff
                    if attempt < MACRO_SMTP_MAX_RETRIES:
                        sleep_time = MACRO_SMTP_RETRY_BACKOFF_SEG * attempt
                        logger.info(f"[SMTP] Aguardando {sleep_time}s antes da próxima tentativa...")
                        time.sleep(sleep_time)

                # Se esgotou os retries e não retornou True, falhou definitivamente.
                final_exc = (
                    last_exc
                    if last_exc is not None
                    else RuntimeError("Falha SMTP após esgotar tentativas sem exceção registrada.")
                )
                smtp_details = extract_smtp_error_details(
                    final_exc, raw_email=email, masked_email=masked_email
                )
                failed_attrs: Dict[str, Any] = {
                    **base_metric_attrs,
                    "email.failure_stage": "smtp_retries_exhausted",
                    "email.error_type": type(final_exc).__name__,
                    "smtp.attempts": MACRO_SMTP_MAX_RETRIES,
                    "smtp.account_slot": account_slot,
                }
                if "smtp_code" in smtp_details:
                    failed_attrs["smtp.code"] = smtp_details["smtp_code"]
                record_email_dispatch_failed(failed_attrs)
                capture_email_dispatch_error(
                    final_exc,
                    failure_stage="smtp_retries_exhausted",
                    tags={
                        "email.provider": "smtp",
                        "email.channel": channel,
                        "smtp.account_slot": account_slot,
                    },
                    smtp_context={
                        "host": self.host,
                        "port": self.port,
                        "channel": channel,
                        "account_slot": account_slot,
                        "attempts": MACRO_SMTP_MAX_RETRIES,
                        "max_retries": MACRO_SMTP_MAX_RETRIES,
                        "recipient_domain": recipient_domain,
                        "message_id": msg["Message-ID"],
                        "retry_history": retry_history,
                        **smtp_details,
                    },
                    raw_email=email,
                    masked_email=masked_email,
                )
                logger.error(
                    f"[SMTP] Falha definitiva ao enviar e-mail para {masked_email} após {MACRO_SMTP_MAX_RETRIES} tentativas.",
                    exc_info=final_exc,
                )
                return False

        except Exception as e:
            record_email_dispatch_failed(
                {
                    **base_metric_attrs,
                    "email.failure_stage": "smtp_fatal",
                    "email.error_type": type(e).__name__,
                }
            )
            capture_email_dispatch_error(
                e,
                failure_stage="smtp_fatal",
                tags={"email.provider": "smtp", "email.channel": channel},
                smtp_context={
                    "host": self.host,
                    "port": self.port,
                    "channel": channel,
                    "recipient_domain": recipient_domain,
                },
                raw_email=email,
                masked_email=masked_email,
            )
            sanitized_fatal = sanitize_error_message(
                str(e), raw_email=email, masked_email=masked_email
            )
            logger.error(
                f"Erro fatal ao formatar/enviar e-mail via SMTP para {masked_email}: {sanitized_fatal}",
                exc_info=e,
            )
            return False
