import smtplib
import logging
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional
import re
import os
import mimetypes
import uuid
from src.domain.interfaces import MessageProviderProtocol
from src.core.macros import MACRO_SMTP_THROTTLE_DELAY_SEG, MACRO_SMTP_MAX_RETRIES, MACRO_SMTP_RETRY_BACKOFF_SEG

logger = logging.getLogger(__name__)

class SMTPEmailProvider(MessageProviderProtocol):
    """
    Adaptador concreto para envio de E-mail utilizando o protocolo SMTP.
    Suporta conexão segura via SSL ou TLS (portas 465/587).
    Mantém uma única conexão TCP/SMTP viva (Stateful/Pooling), gerencia concorrência com Lock (Throttling) e 
    fornece mecanismo de Retry com Exponential Backoff.
    """
    def __init__(self, host: str, port: int, user: Optional[str], password: Optional[str], from_addr: Optional[str]):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr or user or "recuperacao@sualoja.com"
        
        self._lock = threading.Lock()
        self._server = None

    def _connect(self) -> None:
        """
        Garante que o cliente SMTP está conectado e logado.
        Não é thread-safe por si só; deve ser chamado de dentro do self._lock.
        """
        if self._server is not None:
            try:
                status = self._server.noop()[0]
                if status == 250:
                    return
            except smtplib.SMTPServerDisconnected:
                self._server = None
            except Exception as e:
                logger.warning(f"[SMTP] Erro inesperado ao verificar conexão viva (noop): {e}")
                self._server = None

        if self._server is None:
            if self.port == 465:
                logger.info(f"Estabelecendo nova conexão SMTP segura (SSL) com {self.host}:{self.port}...")
                self._server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                logger.info(f"Estabelecendo nova conexão SMTP (STARTTLS) com {self.host}:{self.port}...")
                self._server = smtplib.SMTP(self.host, self.port, timeout=15)
                self._server.starttls()
            
            if self.user and self.password:
                logger.info(f"Autenticando usuário SMTP '{self.user}'...")
                self._server.login(self.user, self.password)

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        parts = email.split('@')
        masked_email = f"{parts[0][0]}***@{parts[1]}" if len(parts) == 2 and len(parts[0]) > 0 else "***@***"
        
        try:
            # Container raiz (related) para permitir imagens inline e HTML
            msg_root = MIMEMultipart("related")
            msg_root["Subject"] = subject
            msg_root["From"] = self.from_addr
            msg_root["To"] = email
            msg_root.set_charset("utf-8")
            
            # Container alternativo para o texto html/plano
            msg_alternative = MIMEMultipart("alternative")
            msg_root.attach(msg_alternative)
            
            # Parse HTML for local files (file:///)
            images_to_attach = []
            html_processed = html_body
            
            # Regex to find local file paths in src or background attributes
            # Matches anything that doesn't start with http, https, cid:, data:, mailto:
            pattern = r'(?:src|background)=["\'](?!http|https|cid:|data:|mailto:)([^"\']+)["\']'
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            
            for match in re.finditer(pattern, html_body):
                full_url = match.group(1) # e.g. "src/templates/emails/..."
                
                # Resolve filepath
                if full_url.startswith('file://'):
                    filepath = full_url.replace('file://', '', 1)
                elif full_url.startswith('/'):
                    filepath = full_url
                else:
                    filepath = os.path.join(project_root, full_url)
                
                if not os.path.exists(filepath):
                    logger.warning(f"Imagem local não encontrada para anexar: {filepath}")
                    continue
                
                # Gera CID unico seguro
                cid = f"img_{uuid.uuid4().hex[:8]}"
                
                # Substitui a url exata no html
                html_processed = html_processed.replace(f'"{full_url}"', f'"cid:{cid}"').replace(f"'{full_url}'", f"'cid:{cid}'")
                images_to_attach.append((cid, filepath))
            
            # Adiciona o HTML (agora com CIDs) na parte alternativa
            part = MIMEText(html_processed, "html", "utf-8")
            msg_alternative.attach(part)
            
            # Anexa as imagens reais no root (related)
            for cid, filepath in images_to_attach:
                try:
                    with open(filepath, 'rb') as f:
                        img_data = f.read()
                    
                    # Tenta descobrir o mime type, padrão jpeg
                    mime_guess, _ = mimetypes.guess_type(filepath)
                    subtype = mime_guess.split('/')[1] if mime_guess else 'jpeg'
                    
                    img = MIMEImage(img_data, _subtype=subtype)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline')
                    msg_root.attach(img)
                except Exception as e:
                    logger.warning(f"Erro ao anexar imagem inline ({filepath}): {e}")
            
            with self._lock:
                for attempt in range(1, MACRO_SMTP_MAX_RETRIES + 1):
                    try:
                        self._connect()
                        
                        logger.info(f"Despachando mensagem SMTP para {masked_email}...")
                        self._server.sendmail(self.from_addr, [email], msg_root.as_string())
                        
                        logger.info(f"E-mail enviado com sucesso via SMTP para: {masked_email}")
                        
                        # Throttle/Rate Limit
                        time.sleep(MACRO_SMTP_THROTTLE_DELAY_SEG)
                        return True
                        
                    except smtplib.SMTPServerDisconnected as e:
                        logger.warning(f"[SMTP] Conexão caiu na tentativa {attempt}/{MACRO_SMTP_MAX_RETRIES}: {e}")
                        self._server = None
                    except (smtplib.SMTPException, OSError, TimeoutError) as e:
                        logger.warning(f"[SMTP] Erro transitório na tentativa {attempt}/{MACRO_SMTP_MAX_RETRIES} para {masked_email}: {e}")
                        self._server = None
                    
                    # Se não for a última tentativa, aplica o backoff
                    if attempt < MACRO_SMTP_MAX_RETRIES:
                        sleep_time = MACRO_SMTP_RETRY_BACKOFF_SEG * attempt
                        logger.info(f"[SMTP] Aguardando {sleep_time}s antes da próxima tentativa...")
                        time.sleep(sleep_time)
                
                # Se esgotou os retries e não retornou True, falhou miseravelmente.
                logger.error(f"[SMTP] Falha definitiva ao enviar e-mail para {masked_email} após {MACRO_SMTP_MAX_RETRIES} tentativas.")
                return False
                
        except Exception as e:
            logger.error(f"Erro fatal ao formatar/enviar e-mail via SMTP para {masked_email}: {e}", exc_info=True)
            return False
