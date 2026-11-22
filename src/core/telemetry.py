"""
Módulo centralizado de telemetria e observabilidade para disparos de e-mail via Sentry.

Responsável por:
- Emitir métricas de aplicação (contadores de início, envio confirmado e falha);
- Isolar contexto e atributos por disparo (LGPD: zero PII);
- Abrir spans de performance para operações SMTP;
- Registrar breadcrumbs de tentativas e falhas transitórias;
- Capturar exceções preservando traceback completo sem duplicação de issues;
- Garantir política Zero-Crash em qualquer falha do SDK ou ausência de DSN,
  sem jamais engolir exceções de negócio do bloco monitorado.
"""

from contextlib import contextmanager
import re
import smtplib
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

try:
    import sentry_sdk
except ImportError:  # pragma: no cover - fallback caso o pacote não esteja instalado
    sentry_sdk = None

METRIC_EMAIL_DISPATCH_STARTED = "email.dispatch.started"
METRIC_EMAIL_DISPATCH_SENT = "email.dispatch.sent"
METRIC_EMAIL_DISPATCH_FAILED = "email.dispatch.failed"
METRIC_DAEMON_CYCLE_COMPLETED = "daemon.cycle.completed"
METRIC_DAEMON_CYCLE_DURATION = "daemon.cycle.duration"

EMAIL_TYPE_BY_TEMPLATE: Dict[str, str] = {
    "pedido_aprovado": "order_payment_confirmed",
    "pedido_pendente": "order_payment_pending",
    "pedido_a_caminho": "order_shipped_tracking",
    "cupom_pedido_1": "order_recovery_coupon_10",
    "cupom_pedido_2": "order_recovery_coupon_15",
    "cupom_pedido_3": "order_recovery_coupon_20",
    "carrinho_abandonado_cupom4": "cart_abandoned_reminder",
    "carrinho_abandonado_cupom5": "cart_recovery_coupon_1",
    "carrinho_abandonado_cupom6": "cart_recovery_coupon_2",
}


def resolve_email_type(
    template_name: Optional[str],
    email_type: Optional[str] = None,
) -> str:
    """
    Resolve a flag semântica `email.type` para observabilidade no Sentry a partir
    de um valor explícito ou do mapeamento oficial por `template_name`.
    """
    if isinstance(email_type, str) and email_type.strip():
        return email_type.strip()
    if isinstance(template_name, str) and template_name.strip():
        return EMAIL_TYPE_BY_TEMPLATE.get(template_name.strip(), "unknown")
    return "unknown"


def extract_recipient_domain(email: Optional[str]) -> str:
    """
    Extrai o domínio em minúsculas após o último '@' do endereço informado.
    Retorna 'unknown' quando o valor for nulo, vazio ou sem domínio válido.
    """
    if not isinstance(email, str):
        return "unknown"

    cleaned = email.strip()
    if not cleaned or "@" not in cleaned:
        return "unknown"

    local_part, domain = cleaned.rsplit("@", 1)
    domain = domain.strip().lower()
    if (
        not local_part.strip()
        or not domain
        or "." not in domain
        or domain.startswith(".")
        or domain.endswith(".")
        or ".." in domain
        or any(ch.isspace() for ch in domain)
        or "<" in domain
        or ">" in domain
    ):
        return "unknown"

    return domain


def sanitize_error_message(
    message: str,
    raw_email: Optional[str] = None,
    masked_email: Optional[str] = None,
) -> str:
    """
    Substitui ocorrências do e-mail cru (case-insensitive) por sua versão mascarada
    para manter conformidade LGPD em logs, contextos e payloads do Sentry.
    """
    text = message if isinstance(message, str) else str(message)
    if not isinstance(raw_email, str):
        return text

    raw_clean = raw_email.strip()
    if not raw_clean:
        return text

    replacement = masked_email or "***@***"
    if raw_clean != raw_email:
        text = re.sub(re.escape(raw_email), lambda _: replacement, text, flags=re.IGNORECASE)
    text = re.sub(re.escape(raw_clean), lambda _: replacement, text, flags=re.IGNORECASE)
    return text


def _decode_smtp_error_text(raw_err: Any) -> str:
    """Decodifica payloads de erro SMTP (bytes ou qualquer objeto) em string UTF-8 segura."""
    if isinstance(raw_err, bytes):
        return raw_err.decode("utf-8", errors="replace")
    return str(raw_err)


def extract_smtp_error_details(
    exc: BaseException,
    raw_email: Optional[str] = None,
    masked_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extrai código e mensagem sanitizada de exceções SMTP conhecidas sem expor PII.
    """
    if isinstance(exc, smtplib.SMTPRecipientsRefused):
        recipients = getattr(exc, "recipients", None)
        if not isinstance(recipients, dict) or not recipients:
            return {}

        first_entry = next(iter(recipients.values()), None)
        if not isinstance(first_entry, (tuple, list)) or len(first_entry) < 2:
            return {}

        raw_code, raw_err = first_entry[0], first_entry[1]
        details: Dict[str, Any] = {}
        try:
            details["smtp_code"] = int(raw_code)
        except (TypeError, ValueError):
            pass

        err_text = sanitize_error_message(
            _decode_smtp_error_text(raw_err),
            raw_email=raw_email,
            masked_email=masked_email,
        )
        # Redige quaisquer outras chaves de e-mail eventualmente ecoadas na resposta SMTP
        for recipient_key in recipients.keys():
            if isinstance(recipient_key, str) and "@" in recipient_key:
                err_text = sanitize_error_message(
                    err_text,
                    raw_email=recipient_key,
                    masked_email=masked_email or "***@***",
                )
        details["smtp_error"] = err_text
        return details

    if isinstance(exc, smtplib.SMTPResponseException):
        details = {}
        smtp_code = getattr(exc, "smtp_code", None)
        if smtp_code is not None:
            try:
                details["smtp_code"] = int(smtp_code)
            except (TypeError, ValueError):
                pass

        smtp_error = getattr(exc, "smtp_error", None)
        if smtp_error is not None:
            details["smtp_error"] = sanitize_error_message(
                _decode_smtp_error_text(smtp_error),
                raw_email=raw_email,
                masked_email=masked_email,
            )
        return details

    return {}


def _sanitize_with_emails(
    text: str,
    raw_emails: Iterable[str],
    masked_email: Optional[str] = None,
) -> str:
    """Aplica `sanitize_error_message` para todos os e-mails crus fornecidos."""
    result = text
    for candidate in raw_emails:
        result = sanitize_error_message(result, raw_email=candidate, masked_email=masked_email)
    return result


def _sanitize_nested_value(
    value: Any,
    raw_email: Optional[str] = None,
    masked_email: Optional[str] = None,
    extra_raw_emails: Optional[Iterable[str]] = None,
) -> Any:
    """Sanitiza recursivamente strings em dicionários, listas e tuplas sem alterar tipos primitivos."""
    raw_emails: List[str] = []
    for candidate in [raw_email, *(extra_raw_emails or [])]:
        if isinstance(candidate, str) and candidate.strip() and candidate not in raw_emails:
            raw_emails.append(candidate)

    if not raw_emails:
        return value

    if isinstance(value, str):
        return _sanitize_with_emails(value, raw_emails, masked_email=masked_email)
    if isinstance(value, dict):
        return {
            _sanitize_with_emails(str(k), raw_emails, masked_email=masked_email)
            if isinstance(k, str)
            else k: _sanitize_nested_value(
                v,
                raw_email=raw_email,
                masked_email=masked_email,
                extra_raw_emails=extra_raw_emails,
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            _sanitize_nested_value(
                item,
                raw_email=raw_email,
                masked_email=masked_email,
                extra_raw_emails=extra_raw_emails,
            )
            for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            _sanitize_nested_value(
                item,
                raw_email=raw_email,
                masked_email=masked_email,
                extra_raw_emails=extra_raw_emails,
            )
            for item in value
        )
    return value


@contextmanager
def email_dispatch_scope(
    *,
    flow: str,
    template_name: str,
    stage: str,
    entity_type: str,
    entity_id: str,
    is_promotional: bool,
    dispatch_kind: str = "primary",
    order_number: Optional[str] = None,
    cart_id: Optional[str] = None,
    recipient_domain: str = "unknown",
    email_type: Optional[str] = None,
) -> Iterator[None]:
    """
    Abre um escopo isolado do Sentry para enriquecer métricas, spans e erros do disparo
    sem expor PII. Falhas do Sentry SDK nunca interrompem o fluxo nem silenciam exceções de negócio.
    """
    channel = "promotional" if is_promotional else "transactional"
    resolved_email_type = resolve_email_type(template_name, email_type)
    safe_domain = (
        recipient_domain.strip().lower()
        if isinstance(recipient_domain, str) and recipient_domain.strip()
        else "unknown"
    )
    safe_entity_id = str(entity_id)

    context_dict: Dict[str, Any] = {
        "flow": flow,
        "template_name": template_name,
        "email_type": resolved_email_type,
        "stage": stage,
        "channel": channel,
        "dispatch_kind": dispatch_kind,
        "entity_type": entity_type,
        "entity_id": safe_entity_id,
        "recipient_domain": safe_domain,
    }
    if order_number is not None and str(order_number).strip():
        context_dict["order_number"] = str(order_number)
    if cart_id is not None and str(cart_id).strip():
        context_dict["cart_id"] = str(cart_id)

    cm = None
    entered = False
    try:
        if sentry_sdk is not None:
            cm = sentry_sdk.new_scope()
            scope = cm.__enter__()
            entered = True
            if scope is not None:
                scope.set_tag("email.flow", flow)
                scope.set_tag("email.template", template_name)
                scope.set_tag("email.type", resolved_email_type)
                scope.set_tag("email.stage", stage)
                scope.set_tag("email.channel", channel)
                scope.set_tag("email.dispatch_kind", dispatch_kind)

                if hasattr(scope, "set_attribute"):
                    scope.set_attribute("email.flow", flow)
                    scope.set_attribute("email.template", template_name)
                    scope.set_attribute("email.type", resolved_email_type)
                    scope.set_attribute("email.stage", stage)
                    scope.set_attribute("email.channel", channel)
                    scope.set_attribute("email.dispatch_kind", dispatch_kind)
                    scope.set_attribute("email.entity_type", entity_type)
                    scope.set_attribute("email.entity_id", safe_entity_id)
                    scope.set_attribute("email.recipient_domain", safe_domain)
                    if "order_number" in context_dict:
                        scope.set_attribute("email.order_number", context_dict["order_number"])
                    if "cart_id" in context_dict:
                        scope.set_attribute("email.cart_id", context_dict["cart_id"])

                scope.set_context("email_dispatch", context_dict)
    except Exception:
        if entered and cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass
        cm = None
        entered = False

    if not entered or cm is None:
        yield
        return

    try:
        yield
    except BaseException as exc:
        try:
            cm.__exit__(type(exc), exc, exc.__traceback__)
        except Exception:
            pass
        raise
    else:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


@contextmanager
def start_smtp_span(
    name: str,
    data: Optional[Dict[str, Any]] = None,
) -> Iterator[Any]:
    """
    Abre um span Sentry (`op="email.smtp.send"`) com metadados não-PII.
    Propaga integralmente quaisquer exceções ocorridas no bloco interno.
    """
    cm = None
    entered = False
    span = None
    try:
        if sentry_sdk is not None:
            cm = sentry_sdk.start_span(op="email.smtp.send", name=name)
            span = cm.__enter__()
            entered = True
            if span is not None and data and hasattr(span, "set_data"):
                for key, value in data.items():
                    if value is not None:
                        span.set_data(key, value)
    except Exception:
        if entered and cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass
        cm = None
        entered = False
        span = None

    if not entered or cm is None:
        yield None
        return

    try:
        yield span
    except BaseException as exc:
        try:
            cm.__exit__(type(exc), exc, exc.__traceback__)
        except Exception:
            pass
        raise
    else:
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


def add_smtp_retry_breadcrumb(
    *,
    attempt: int,
    max_retries: int,
    error_type: str,
    smtp_code: Optional[int],
    channel: str,
    recipient_domain: str,
    email_type: Optional[str] = None,
) -> None:
    """Registra breadcrumb estruturado para cada tentativa SMTP que falhou."""
    try:
        if sentry_sdk is None:
            return
        data: Dict[str, Any] = {
            "attempt": attempt,
            "max_retries": max_retries,
            "error_type": error_type,
            "channel": channel,
            "recipient_domain": recipient_domain,
        }
        if isinstance(email_type, str) and email_type.strip():
            data["email_type"] = email_type.strip()
        if smtp_code is not None:
            data["smtp_code"] = smtp_code
        sentry_sdk.add_breadcrumb(
            category="smtp.retry",
            message=f"Tentativa SMTP {attempt}/{max_retries} falhou ({error_type})",
            level="warning",
            data=data,
        )
    except Exception:
        pass


def _record_counter(
    metric_name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> None:
    """Emite contador de métrica no Sentry filtrando valores nulos (Zero-Crash)."""
    try:
        if sentry_sdk is None or not hasattr(sentry_sdk, "metrics"):
            return
        clean_attrs = (
            {k: v for k, v in attributes.items() if v is not None}
            if attributes
            else {}
        )
        sentry_sdk.metrics.count(metric_name, 1, attributes=clean_attrs)
    except Exception:
        pass


def record_email_dispatch_started(attributes: Optional[Dict[str, Any]] = None) -> None:
    """Registra incremento do contador `email.dispatch.started`."""
    _record_counter(METRIC_EMAIL_DISPATCH_STARTED, attributes)


def record_email_dispatch_sent(attributes: Optional[Dict[str, Any]] = None) -> None:
    """Registra incremento do contador `email.dispatch.sent`."""
    _record_counter(METRIC_EMAIL_DISPATCH_SENT, attributes)


def record_email_dispatch_failed(attributes: Optional[Dict[str, Any]] = None) -> None:
    """Registra incremento do contador `email.dispatch.failed`."""
    _record_counter(METRIC_EMAIL_DISPATCH_FAILED, attributes)


def record_daemon_cycle_metrics(
    status: str,
    duration_seconds: float,
    monitor_slug: str = "yampi-daemon-cycle",
) -> None:
    """Emite contador e distribuição de duração do ciclo do daemon no Sentry (Zero-Crash)."""
    try:
        if sentry_sdk is None or not hasattr(sentry_sdk, "metrics"):
            return
        attrs = {
            "monitor.slug": monitor_slug,
            "status": status,
        }
        sentry_sdk.metrics.count(METRIC_DAEMON_CYCLE_COMPLETED, 1, attributes=attrs)
        if hasattr(sentry_sdk.metrics, "distribution"):
            sentry_sdk.metrics.distribution(
                METRIC_DAEMON_CYCLE_DURATION,
                max(0.0, float(duration_seconds)),
                unit="second",
                attributes=attrs,
            )
    except Exception:
        pass


_REDACTED_FRAME_VAR_KEYS = frozenset(
    {
        "html",
        "html_body",
        "html_processed",
        "items_html",
        "plain_text",
        "resolved_plain_text",
        "content",
        "msg",
        "raw_msg",
        "msg_copy",
        "flatmsg",
        "bytesmsg",
        "event",
        "customer",
        "customer_data",
        "order_data",
        "cart_data",
        "data",
        "metadata",
        "template_data",
        "context",
        "without_blocks",
        "without_tags",
        "args",
        "kwargs",
        "email",
        "raw_email",
        "recipient_email",
        "to_addrs",
        "senderrs",
        "recip",
        "each",
        "addr_fields",
        "cpf",
        "pix_code",
    }
)
_REDACTED_KEY_SUBSTRINGS = ("password", "secret", "token", "auth")
_REDACTED_VALUE_MARKERS = (
    "<html",
    "<!doctype",
    "ordertransitionevent",
    "carttransitionevent",
    "customer_data",
)


def _is_sensitive_frame_key(key: Any) -> bool:
    """Identifica nomes de variáveis locais sensíveis ou extensas em frames de stacktrace."""
    if not isinstance(key, str):
        return False
    lowered = key.strip().lower()
    if lowered in _REDACTED_FRAME_VAR_KEYS:
        return True
    return any(sub in lowered for sub in _REDACTED_KEY_SUBSTRINGS)


def _sanitize_frame_var_value(
    value: Any,
    raw_emails: List[str],
    masked_email: Optional[str],
) -> Any:
    """Redige conteúdos HTML, payloads de evento e e-mails dentro de `frame['vars']`."""
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _REDACTED_VALUE_MARKERS):
            return "[REDACTED]"
        return _sanitize_with_emails(value, raw_emails, masked_email=masked_email)
    if isinstance(value, dict):
        sanitized: Dict[Any, Any] = {}
        for k, v in value.items():
            safe_k = (
                _sanitize_with_emails(k, raw_emails, masked_email=masked_email)
                if isinstance(k, str)
                else k
            )
            if _is_sensitive_frame_key(k):
                sanitized[safe_k] = "[REDACTED]"
            else:
                sanitized[safe_k] = _sanitize_frame_var_value(v, raw_emails, masked_email)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_frame_var_value(item, raw_emails, masked_email) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_frame_var_value(item, raw_emails, masked_email) for item in value)
    return value


def _sanitize_frame_vars(
    vars_dict: Dict[str, Any],
    raw_emails: List[str],
    masked_email: Optional[str],
) -> Dict[str, Any]:
    """Redige variáveis locais sensíveis em `frame['vars']` mantendo conformidade LGPD."""
    sanitized_vars: Dict[str, Any] = {}
    for var_name, var_value in vars_dict.items():
        if _is_sensitive_frame_key(var_name):
            sanitized_vars[var_name] = "[REDACTED]"
        else:
            sanitized_vars[var_name] = _sanitize_frame_var_value(
                var_value, raw_emails, masked_email
            )
    return sanitized_vars


def _build_pii_sanitizer_processor(
    raw_email: Optional[str],
    masked_email: Optional[str],
    extra_raw_emails: Optional[Iterable[str]] = None,
):
    """Cria um event processor por escopo para mascarar PII e redigir variáveis locais sensíveis."""
    raw_emails: List[str] = []
    for candidate in [raw_email, *(extra_raw_emails or [])]:
        if isinstance(candidate, str) and candidate.strip() and candidate not in raw_emails:
            raw_emails.append(candidate)

    def _processor(event: Dict[str, Any], hint: Any) -> Dict[str, Any]:
        try:
            if not isinstance(event, dict):
                return event

            exception_section = event.get("exception")
            if isinstance(exception_section, dict) and isinstance(exception_section.get("values"), list):
                for exc_val in exception_section["values"]:
                    if not isinstance(exc_val, dict):
                        continue
                    if isinstance(exc_val.get("value"), str) and raw_emails:
                        exc_val["value"] = _sanitize_with_emails(
                            exc_val["value"], raw_emails, masked_email=masked_email
                        )
                    stacktrace = exc_val.get("stacktrace")
                    if isinstance(stacktrace, dict) and isinstance(stacktrace.get("frames"), list):
                        for frame in stacktrace["frames"]:
                            if isinstance(frame, dict) and isinstance(frame.get("vars"), dict):
                                frame["vars"] = _sanitize_frame_vars(
                                    frame["vars"], raw_emails, masked_email
                                )

            if raw_emails:
                logentry = event.get("logentry")
                if isinstance(logentry, dict):
                    for field in ("message", "formatted"):
                        if isinstance(logentry.get(field), str):
                            logentry[field] = _sanitize_with_emails(
                                logentry[field], raw_emails, masked_email=masked_email
                            )

                if isinstance(event.get("message"), str):
                    event["message"] = _sanitize_with_emails(
                        event["message"], raw_emails, masked_email=masked_email
                    )

                for section_key in ("breadcrumbs", "contexts", "extra", "tags"):
                    if section_key in event and event[section_key] is not None:
                        event[section_key] = _sanitize_nested_value(
                            event[section_key],
                            raw_email=raw_email,
                            masked_email=masked_email,
                            extra_raw_emails=extra_raw_emails,
                        )
        except Exception:
            return event
        return event

    return _processor


def capture_email_dispatch_error(
    exc: BaseException,
    *,
    failure_stage: str,
    tags: Optional[Dict[str, str]] = None,
    smtp_context: Optional[Dict[str, Any]] = None,
    raw_email: Optional[str] = None,
    masked_email: Optional[str] = None,
    extra_raw_emails: Optional[Iterable[str]] = None,
) -> None:
    """
    Captura uma exceção de disparo no Sentry herdando o escopo atual e anexando
    tags de falha, detalhes SMTP sanitizados e defesa em profundidade contra vazamento de PII.
    """
    try:
        if sentry_sdk is None:
            return

        details = extract_smtp_error_details(
            exc, raw_email=raw_email, masked_email=masked_email
        )

        with sentry_sdk.new_scope() as scope:
            if scope is not None:
                scope.set_tag("email.failure_stage", failure_stage)
                scope.set_tag("email.error_type", type(exc).__name__)
                if "smtp_code" in details:
                    scope.set_tag("smtp.code", str(details["smtp_code"]))

                if tags:
                    for key, value in tags.items():
                        if value is not None:
                            scope.set_tag(key, str(value))

                if smtp_context is not None:
                    sanitized_context = _sanitize_nested_value(
                        smtp_context,
                        raw_email=raw_email,
                        masked_email=masked_email,
                        extra_raw_emails=extra_raw_emails,
                    )
                    scope.set_context("smtp_dispatch", sanitized_context)

                scope.add_event_processor(
                    _build_pii_sanitizer_processor(
                        raw_email, masked_email, extra_raw_emails=extra_raw_emails
                    )
                )

            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def flush_telemetry(timeout: float = 5.0) -> None:
    """Força o envio dos buffers de métricas, spans e eventos pendentes do Sentry."""
    try:
        if sentry_sdk is None:
            return
        sentry_sdk.flush(timeout=timeout)
    except Exception:
        pass
