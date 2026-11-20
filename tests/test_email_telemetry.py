"""Testes TDD da telemetria transacional de e-mail (Sentry Metrics, Spans, Issues e LGPD)."""

from concurrent.futures import ThreadPoolExecutor
import json
import logging
import smtplib
import threading
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
import sentry_sdk
from sentry_sdk.client import NonRecordingClient
from sentry_sdk.transport import Transport

import src.main as app_main
from src.core import logging_config, macros
from src.core.config import Config
from src.core.telemetry import (
    METRIC_EMAIL_DISPATCH_FAILED,
    METRIC_EMAIL_DISPATCH_SENT,
    METRIC_EMAIL_DISPATCH_STARTED,
    add_smtp_retry_breadcrumb,
    capture_email_dispatch_error,
    email_dispatch_scope,
    extract_recipient_domain,
    extract_smtp_error_details,
    flush_telemetry,
    record_email_dispatch_failed,
    record_email_dispatch_sent,
    record_email_dispatch_started,
    sanitize_error_message,
    start_smtp_span,
)
from src.domain.events import CartTransitionEvent, OrderTransitionEvent
from src.ports.message_provider import DryRunMessageProvider
from src.ports.smtp_email_provider import SMTPEmailProvider
from src.services.notification_service import NotificationService


class DummyTransport(Transport):
    """Transporte em memória thread-safe que captura envelopes reais do sentry-sdk."""

    def __init__(self, options: Dict[str, Any] | None = None) -> None:
        super().__init__(options)
        self._lock = threading.Lock()
        self.envelopes: List[Any] = []

    def capture_envelope(self, envelope: Any) -> None:
        with self._lock:
            self.envelopes.append(envelope)

    def _itens_por_tipo(self, tipo_item: str) -> List[Dict[str, Any]]:
        resultados: List[Dict[str, Any]] = []
        with self._lock:
            envelopes_snapshot = list(self.envelopes)
        for envelope in envelopes_snapshot:
            for item in envelope.items:
                if item.type == tipo_item:
                    resultados.append(json.loads(item.get_bytes().decode("utf-8")))
        return resultados

    def metrics(self) -> List[Dict[str, Any]]:
        """Retorna todos os itens de métrica `trace_metric` capturados nos envelopes."""
        metricas: List[Dict[str, Any]] = []
        for payload in self._itens_por_tipo("trace_metric"):
            metricas.extend(payload.get("items", []))
        return metricas

    def metrics_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Filtra métricas capturadas pelo nome canônico."""
        return [m for m in self.metrics() if m.get("name") == name]

    def events(self) -> List[Dict[str, Any]]:
        """Retorna todos os eventos de erro/issue capturados nos envelopes."""
        return self._itens_por_tipo("event")

    def transactions(self) -> List[Dict[str, Any]]:
        """Retorna todas as transações APM capturadas nos envelopes."""
        return self._itens_por_tipo("transaction")

    def serialized_payloads(self) -> str:
        """Serializa todos os envelopes para verificação de ausência de PII (LGPD)."""
        partes: List[str] = []
        with self._lock:
            envelopes_snapshot = list(self.envelopes)
        for envelope in envelopes_snapshot:
            for item in envelope.items:
                partes.append(item.get_bytes().decode("utf-8", errors="replace"))
        return "\n".join(partes)


def _attr_val(metric: Dict[str, Any], key: str) -> Any:
    """Extrai o valor tipado de um atributo no payload `trace_metric` do sentry-sdk v2."""
    attr = metric.get("attributes", {}).get(key)
    if isinstance(attr, dict) and "value" in attr:
        return attr["value"]
    return attr


@pytest.fixture
def sentry_dummy_transport():
    """Inicializa o Sentry SDK com DummyTransport real e restaura o cliente ao final."""
    global_scope = sentry_sdk.get_global_scope()
    isolation_scope = sentry_sdk.get_isolation_scope()
    prev_client = global_scope.client
    prev_init_flag = logging_config._SENTRY_INITIALIZED

    transport = DummyTransport({"dsn": "https://public@example.ingest.sentry.io/1"})
    sentry_sdk.init(
        dsn="https://public@example.ingest.sentry.io/1",
        transport=transport,
        traces_sample_rate=1.0,
        send_default_pii=False,
        environment="test",
    )
    try:
        yield transport
    finally:
        try:
            sentry_sdk.flush(timeout=2.0)
        finally:
            global_scope.set_client(prev_client)
            isolation_scope.clear()
            logging_config._SENTRY_INITIALIZED = prev_init_flag


@pytest.fixture(autouse=True)
def _isolamento_macros(monkeypatch):
    """Garante que macros globais de redirecionamento e HTML em disco fiquem isoladas."""
    monkeypatch.setattr(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", False)
    monkeypatch.setattr(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", False)
    monkeypatch.setattr(macros, "MACRO_ENABLE_LOCAL_HTML_SAVING", False)


def _criar_config_teste() -> Config:
    return Config(
        YAMPI_USER_TOKEN="tok-teste",
        YAMPI_USER_SECRET_KEY="sec-teste",
        YAMPI_ALIAS="eleveme",
        TEST_EMAIL_RECIPIENT="supervisao@elevemeloja.com.br",
        SMTP_HOST="smtp.elevemeloja.com.br",
        SMTP_PORT=465,
        SMTP_USER="oficial@elevemeloja.com.br",
        SMTP_PASSWORD="senha-oficial-segura",
        SMTP_FROM="oficial@elevemeloja.com.br",
        PROMO_SMTP_USER="comercial@elevemeloja.com.br",
        PROMO_SMTP_PASSWORD="senha-comercial-segura",
        PROMO_SMTP_FROM="comercial@elevemeloja.com.br",
    )


def _criar_provider(tmp_path) -> SMTPEmailProvider:
    return SMTPEmailProvider(
        host="smtp.elevemeloja.com.br",
        port=465,
        user="oficial@elevemeloja.com.br",
        password="senha-oficial-segura",
        from_addr="oficial@elevemeloja.com.br",
        promo_user="comercial@elevemeloja.com.br",
        promo_password="senha-comercial-segura",
        promo_from_addr="comercial@elevemeloja.com.br",
        assets_dir=str(tmp_path),
    )


def _criar_evento_pedido(
    order_id: str = "101",
    order_number: str = "PED-101",
    stg: int = 2,
    email: str = "maria.cliente@exemplo.com",
    cart_id: str | None = "CART-999",
) -> OrderTransitionEvent:
    metadata = {"data": [{"key": "cart_id", "value": cart_id}]} if cart_id is not None else {}
    return OrderTransitionEvent(
        order_id=order_id,
        order_number=order_number,
        new_stg=stg,
        customer_data={
            "name": "Maria Silva",
            "first_name": "Maria",
            "email": email,
        },
        order_data={
            "id": order_id,
            "number": order_number,
            "value_total": 199.90,
            "status_url": f"https://elevemeloja.com.br/pedido/{order_id}",
            "checkout_url": f"https://elevemeloja.com.br/checkout/{order_id}",
            "tracking_code": "BR123456789XX",
            "tracking_url": "https://rastreio.exemplo.com/BR123456789XX",
            "metadata": metadata,
            "items": {"data": [{"item_sku": "SKU-1", "title": "Palmilha", "price": 199.90, "quantity": 1}]},
        },
    )


def _criar_evento_carrinho(
    cart_id: str = "CART-202",
    stc: int = 15,
    email: str = "joao.cliente@exemplo.com",
) -> CartTransitionEvent:
    return CartTransitionEvent(
        cart_id=cart_id,
        new_stc=stc,
        customer_data={
            "name": "João Souza",
            "first_name": "João",
            "email": email,
        },
        cart_data={
            "id": cart_id,
            "simulate_url": f"https://elevemeloja.com.br/recuperar/{cart_id}",
            "value_total": 149.90,
            "items": {"data": [{"item_sku": "SKU-2", "title": "Meia", "price": 149.90, "quantity": 1}]},
        },
    )


# ------------------------------------------------------------------------------
# Testes unitários dos helpers de telemetria e sanitização LGPD
# ------------------------------------------------------------------------------


def test_constantes_e_extract_recipient_domain():
    """Valida nomes canônicos das métricas e extração segura do domínio do destinatário."""
    assert METRIC_EMAIL_DISPATCH_STARTED == "email.dispatch.started"
    assert METRIC_EMAIL_DISPATCH_SENT == "email.dispatch.sent"
    assert METRIC_EMAIL_DISPATCH_FAILED == "email.dispatch.failed"

    assert extract_recipient_domain("Maria.Silva@GMAIL.COM ") == "gmail.com"
    assert extract_recipient_domain("contato@sub.empresa.com.br") == "sub.empresa.com.br"
    assert extract_recipient_domain("estranho@meio@Yahoo.Com.Br") == "yahoo.com.br"
    assert extract_recipient_domain(None) == "unknown"
    assert extract_recipient_domain("") == "unknown"
    assert extract_recipient_domain("   ") == "unknown"
    assert extract_recipient_domain("sem_arroba") == "unknown"
    assert extract_recipient_domain("usuario@") == "unknown"
    assert extract_recipient_domain("@sem_usuario.com") == "unknown"


def test_sanitize_error_message_e_extract_smtp_error_details():
    """Valida mascaramento case-insensitive de e-mail e extração de código/mensagem SMTP."""
    raw = "Vitima+Tag@Gmail.Com"
    masked = "vitim*****g@Gmail.Com"

    msg_sanitizada = sanitize_error_message(
        "Falha ao entregar para VITIMA+TAG@gmail.com e vitima+tag@GMAIL.com",
        raw_email=raw,
        masked_email=masked,
    )
    assert "vitima+tag@gmail.com" not in msg_sanitizada.lower()
    assert masked in msg_sanitizada

    msg_fallback = sanitize_error_message("Erro em cliente@teste.com", raw_email="cliente@teste.com")
    assert "cliente@teste.com" not in msg_fallback
    assert "***@***" in msg_fallback

    # Entrada não-string é convertida com segurança
    assert sanitize_error_message(12345) == "12345"  # type: ignore[arg-type]

    # SMTPRecipientsRefused não pode vazar chave com e-mail cru
    exc_refused = smtplib.SMTPRecipientsRefused(
        {"vitima@gmail.com": (550, b"5.1.1 <VITIMA@GMAIL.COM>: Recipient address rejected")}
    )
    detalhes_refused = extract_smtp_error_details(
        exc_refused,
        raw_email="vitima@gmail.com",
        masked_email="vitim*a@gmail.com",
    )
    assert detalhes_refused["smtp_code"] == 550
    assert "vitima@gmail.com" not in detalhes_refused["smtp_error"].lower()
    assert "vitim*a@gmail.com" in detalhes_refused["smtp_error"]

    # SMTPResponseException / SMTPAuthenticationError
    exc_auth = smtplib.SMTPAuthenticationError(535, b"5.7.8 Auth error for user@exemplo.com")
    detalhes_auth = extract_smtp_error_details(
        exc_auth,
        raw_email="user@exemplo.com",
        masked_email="u**r@exemplo.com",
    )
    assert detalhes_auth["smtp_code"] == 535
    assert "user@exemplo.com" not in detalhes_auth["smtp_error"]
    assert "u**r@exemplo.com" in detalhes_auth["smtp_error"]

    # Exceção genérica retorna dicionário vazio
    assert extract_smtp_error_details(RuntimeError("erro generico")) == {}


# ------------------------------------------------------------------------------
# Cenário 1: Counters, herança de atributos do scope e trace_id compartilhado
# ------------------------------------------------------------------------------


def test_counters_herdam_atributos_do_scope_e_compartilham_trace_id(sentry_dummy_transport):
    """Contadores started/sent/failed emitem counter=1.0 com atributos do scope e trace_id ativo."""
    with sentry_sdk.start_transaction(name="ciclo_teste_telemetry") as tx:
        tx_trace_id = tx.trace_id
        with email_dispatch_scope(
            flow="order",
            template_name="pedido_aprovado",
            stage="STG_2",
            entity_type="order",
            entity_id="9001",
            is_promotional=False,
            dispatch_kind="primary",
            order_number="PED-9001",
            cart_id="CART-9001",
            recipient_domain="exemplo.com",
        ):
            record_email_dispatch_started({"email.provider": "smtp", "nulo_ignorado": None})
            record_email_dispatch_sent({"email.provider": "smtp", "smtp.attempts": 1})
            record_email_dispatch_failed({"email.provider": "smtp", "email.failure_stage": "smtp_retries_exhausted"})

    flush_telemetry(timeout=2.0)

    started = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)
    sent = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)
    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)

    assert len(started) == 1
    assert len(sent) == 1
    assert len(failed) == 1

    for metrica in (started[0], sent[0], failed[0]):
        assert metrica["type"] == "counter"
        assert metrica["value"] == 1.0
        assert metrica["trace_id"] == tx_trace_id
        assert "nulo_ignorado" not in metrica["attributes"]
        assert _attr_val(metrica, "email.provider") == "smtp"
        assert _attr_val(metrica, "email.flow") == "order"
        assert _attr_val(metrica, "email.template") == "pedido_aprovado"
        assert _attr_val(metrica, "email.stage") == "STG_2"
        assert _attr_val(metrica, "email.channel") == "transactional"
        assert _attr_val(metrica, "email.dispatch_kind") == "primary"
        assert _attr_val(metrica, "email.entity_type") == "order"
        assert _attr_val(metrica, "email.entity_id") == "9001"
        assert _attr_val(metrica, "email.order_number") == "PED-9001"
        assert _attr_val(metrica, "email.cart_id") == "CART-9001"
        assert _attr_val(metrica, "email.recipient_domain") == "exemplo.com"


# ------------------------------------------------------------------------------
# Cenário 2: Isolamento concorrente em ThreadPoolExecutor (4 threads)
# ------------------------------------------------------------------------------


def test_isolamento_scope_em_thread_pool_4_threads(sentry_dummy_transport):
    """Múltiplas threads concorrentes não misturam entity_id, template nem contextos no Sentry."""

    def executar_tarefa(idx: int) -> None:
        is_order = idx % 2 == 0
        flow = "order" if is_order else "abandoned_cart"
        template = "pedido_aprovado" if is_order else "carrinho_abandonado_cupom4"
        stage = "STG_2" if is_order else "STC_15"
        entity_type = "order" if is_order else "cart"
        entity_id = f"ent-{idx}"

        with email_dispatch_scope(
            flow=flow,
            template_name=template,
            stage=stage,
            entity_type=entity_type,
            entity_id=entity_id,
            is_promotional=not is_order,
            dispatch_kind="primary",
            order_number=f"PED-{idx}" if is_order else None,
            cart_id=f"CART-{idx}",
            recipient_domain=f"dom{idx}.com",
        ):
            record_email_dispatch_started({"email.provider": "smtp"})
            if idx % 3 == 0:
                try:
                    raise RuntimeError(f"Erro concorrente entidade {entity_id}")
                except RuntimeError as exc:
                    record_email_dispatch_failed({"email.provider": "smtp", "email.failure_stage": "smtp_fatal"})
                    capture_email_dispatch_error(
                        exc,
                        failure_stage="smtp_fatal",
                        smtp_context={"slot": idx},
                    )
            else:
                record_email_dispatch_sent({"email.provider": "smtp", "smtp.attempts": 1})

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(executar_tarefa, range(12)))

    flush_telemetry(timeout=2.0)

    started = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)
    sent = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)
    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)
    eventos = sentry_dummy_transport.events()

    assert len(started) == 12
    assert len(sent) == 8
    assert len(failed) == 4
    assert len(eventos) == 4

    for metrica in started + sent + failed:
        entity_id = _attr_val(metrica, "email.entity_id")
        idx = int(entity_id.split("-")[1])
        esperado_template = "pedido_aprovado" if idx % 2 == 0 else "carrinho_abandonado_cupom4"
        esperado_flow = "order" if idx % 2 == 0 else "abandoned_cart"
        assert _attr_val(metrica, "email.template") == esperado_template
        assert _attr_val(metrica, "email.flow") == esperado_flow
        assert _attr_val(metrica, "email.recipient_domain") == f"dom{idx}.com"

    for evento in eventos:
        ctx = evento["contexts"]["email_dispatch"]
        idx = int(ctx["entity_id"].split("-")[1])
        esperado_template = "pedido_aprovado" if idx % 2 == 0 else "carrinho_abandonado_cupom4"
        assert ctx["template_name"] == esperado_template
        assert evento["tags"]["email.template"] == esperado_template
        assert evento["contexts"]["smtp_dispatch"]["slot"] == idx


# ------------------------------------------------------------------------------
# Cenário 3: Sucesso SMTP direto (ordem exata antes de time.sleep, span, 0 erros)
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_smtp_sucesso_direto_emite_started_e_sent_antes_de_sleep(
    mock_smtp_ssl,
    tmp_path,
    sentry_dummy_transport,
    monkeypatch,
):
    """Sucesso SMTP direto emite started (1), span email.smtp.send e sent (1) ANTES de time.sleep."""
    import src.ports.smtp_email_provider as smtp_mod

    ordem: List[str] = []

    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")

    def fake_sendmail(*args, **kwargs):
        ordem.append("sendmail")
        return {}

    mock_server.sendmail.side_effect = fake_sendmail
    mock_smtp_ssl.return_value = mock_server

    orig_started = smtp_mod.record_email_dispatch_started
    orig_sent = smtp_mod.record_email_dispatch_sent

    def spy_started(attrs=None):
        ordem.append("started")
        return orig_started(attrs)

    def spy_sent(attrs=None):
        ordem.append("sent")
        return orig_sent(attrs)

    def spy_sleep(seconds):
        if threading.get_ident() == thread_id_atual:
            ordem.append("sleep")
        else:
            orig_sleep(seconds)

    orig_sleep = smtp_mod.time.sleep
    thread_id_atual = threading.get_ident()

    with patch.object(smtp_mod, "record_email_dispatch_started", side_effect=spy_started), \
         patch.object(smtp_mod, "record_email_dispatch_sent", side_effect=spy_sent), \
         patch.object(smtp_mod.time, "sleep", side_effect=spy_sleep):
        provider = _criar_provider(tmp_path)
        with sentry_sdk.start_transaction(name="tx_smtp_sucesso"):
            resultado = provider.send_email_message(
                "cliente@exemplo.com",
                "Pedido aprovado",
                "<p>Aprovado</p>",
                plain_text="Aprovado",
                is_promotional=False,
            )

    flush_telemetry(timeout=2.0)

    assert resultado is True
    assert ordem == ["started", "sendmail", "sent", "sleep"]

    started = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)
    sent = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)
    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)

    assert len(started) == 1
    assert len(sent) == 1
    assert len(failed) == 0
    assert len(sentry_dummy_transport.events()) == 0
    assert _attr_val(sent[0], "smtp.attempts") == 1
    assert _attr_val(sent[0], "smtp.account_slot") == "primary"
    assert _attr_val(sent[0], "email.recipient_domain") == "exemplo.com"

    transacoes = sentry_dummy_transport.transactions()
    assert len(transacoes) == 1
    spans = transacoes[0].get("spans", [])
    assert any(span.get("op") == "email.smtp.send" for span in spans)


# ------------------------------------------------------------------------------
# Cenário 4: Retries transitórios com sucesso na 2ª tentativa
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_smtp_retry_transitorio_sucesso_segunda_tentativa(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    sentry_dummy_transport,
    monkeypatch,
):
    """Retry transitório com sucesso na 2ª tentativa emite started=1, sent=1 (attempts=2) e breadcrumb."""
    import src.ports.smtp_email_provider as smtp_mod

    breadcrumbs_registrados: List[Dict[str, Any]] = []
    orig_add_bc = smtp_mod.add_smtp_retry_breadcrumb

    def spy_add_bc(**kwargs):
        breadcrumbs_registrados.append(kwargs)
        return orig_add_bc(**kwargs)

    monkeypatch.setattr(smtp_mod, "add_smtp_retry_breadcrumb", spy_add_bc)

    srv_1 = MagicMock()
    srv_1.sendmail.side_effect = smtplib.SMTPServerDisconnected("Queda temporária")
    srv_2 = MagicMock()
    srv_2.noop.return_value = (250, b"OK")
    srv_2.sendmail.return_value = {}
    mock_smtp_ssl.side_effect = [srv_1, srv_2]

    provider = _criar_provider(tmp_path)
    resultado = provider.send_email_message(
        "cliente@exemplo.com",
        "Cupom 10%",
        "<p>Cupom</p>",
        plain_text="Cupom",
        is_promotional=True,
    )

    flush_telemetry(timeout=2.0)

    assert resultado is True
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)) == 1
    sent = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)
    assert len(sent) == 1
    assert _attr_val(sent[0], "smtp.attempts") == 2
    assert _attr_val(sent[0], "smtp.account_slot") == "promo"
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)) == 0
    assert len(sentry_dummy_transport.events()) == 0

    assert len(breadcrumbs_registrados) == 1
    assert breadcrumbs_registrados[0]["attempt"] == 1
    assert breadcrumbs_registrados[0]["error_type"] == "SMTPServerDisconnected"
    assert breadcrumbs_registrados[0]["channel"] == "promotional"


# ------------------------------------------------------------------------------
# Cenário 5: Retries esgotados (1 única issue, stacktrace, contextos, LGPD)
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_smtp_retries_esgotados_gera_issue_unica_com_traceback_e_contextos_sem_pii(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    sentry_dummy_transport,
):
    """Falha definitiva após retries emite 1 failed, 1 issue única com stacktrace e zero PII."""
    email_secreto = "cliente.secreto@exemplo.com"
    srv_falho = MagicMock()
    srv_falho.sendmail.side_effect = [
        smtplib.SMTPServerDisconnected(f"Queda 1 para {email_secreto}"),
        smtplib.SMTPResponseException(421, f"4.3.0 Ocupado {email_secreto}".encode("utf-8")),
        smtplib.SMTPAuthenticationError(535, f"5.7.8 Auth falhou {email_secreto}".encode("utf-8")),
    ]
    mock_smtp_ssl.return_value = srv_falho

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)
    evento = _criar_evento_pedido(order_id="505", order_number="PED-505", email=email_secreto)

    resultado = service.handle_transition(evento, "pedido_aprovado")

    flush_telemetry(timeout=2.0)

    assert resultado is False
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)) == 1
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)) == 0

    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)
    assert len(failed) == 1
    assert _attr_val(failed[0], "email.failure_stage") == "smtp_retries_exhausted"
    assert _attr_val(failed[0], "email.error_type") == "SMTPAuthenticationError"
    assert _attr_val(failed[0], "smtp.code") == 535

    eventos = sentry_dummy_transport.events()
    assert len(eventos) == 1
    ev = eventos[0]

    frames = ev["exception"]["values"][0]["stacktrace"]["frames"]
    assert len(frames) >= 1

    assert ev["tags"]["email.failure_stage"] == "smtp_retries_exhausted"
    assert ev["tags"]["email.error_type"] == "SMTPAuthenticationError"
    assert ev["tags"]["smtp.code"] == "535"

    assert "email_dispatch" in ev["contexts"]
    assert "smtp_dispatch" in ev["contexts"]
    assert ev["contexts"]["email_dispatch"]["entity_id"] == "505"
    assert len(ev["contexts"]["smtp_dispatch"]["retry_history"]) == macros.MACRO_SMTP_MAX_RETRIES

    breadcrumbs = ev.get("breadcrumbs", {}).get("values", [])
    retry_bcs = [b for b in breadcrumbs if b.get("category") == "smtp.retry"]
    assert len(retry_bcs) == macros.MACRO_SMTP_MAX_RETRIES

    # LGPD: e-mail cru, nome completo, CPF, senha SMTP e HTML não podem aparecer no payload Sentry
    tudo_serializado = sentry_dummy_transport.serialized_payloads()
    tudo_lower = tudo_serializado.lower()
    assert email_secreto not in tudo_lower
    assert "maria silva" not in tudo_lower
    assert "senha-oficial-segura" not in tudo_serializado
    assert "<!doctype" not in tudo_lower
    assert "<html" not in tudo_lower
    assert "<table" not in tudo_lower


# ------------------------------------------------------------------------------
# Cenário 6: sendmail retornando `refused` não vazio
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_smtp_sendmail_refused_nao_emite_sent_e_mascara_email_lgpd(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    sentry_dummy_transport,
):
    """Retorno não vazio de sendmail() falha com SMTPRecipientsRefused sem vazar o e-mail recusado."""
    vitima = "vitima@gmail.com"
    srv = MagicMock()
    srv.noop.return_value = (250, b"OK")
    srv.sendmail.return_value = {vitima: (550, b"5.1.1 User unknown")}
    mock_smtp_ssl.return_value = srv

    provider = _criar_provider(tmp_path)
    resultado = provider.send_email_message(
        vitima,
        "Aviso pedido",
        "<p>Olá</p>",
        plain_text="Olá",
        is_promotional=False,
    )

    flush_telemetry(timeout=2.0)

    assert resultado is False
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)) == 1
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)) == 0

    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)
    assert len(failed) == 1
    assert _attr_val(failed[0], "email.error_type") == "SMTPRecipientsRefused"
    assert _attr_val(failed[0], "smtp.code") == 550

    eventos = sentry_dummy_transport.events()
    assert len(eventos) == 1
    ev = eventos[0]
    assert ev["tags"]["email.error_type"] == "SMTPRecipientsRefused"
    assert ev["tags"]["smtp.code"] == "550"
    assert len(ev["exception"]["values"][0]["stacktrace"]["frames"]) >= 1

    # LGPD estrita: endereço da vítima não pode aparecer em nenhuma métrica, tag ou evento
    assert vitima not in sentry_dummy_transport.serialized_payloads().lower()


# ------------------------------------------------------------------------------
# Cenário 7: Erro fatal inesperado fora do loop de retry (smtp_fatal)
# ------------------------------------------------------------------------------


def test_smtp_erro_fatal_fora_do_loop_emite_smtp_fatal_e_issue_unica(
    tmp_path,
    sentry_dummy_transport,
):
    """Falha inesperada na montagem MIME emite failed (smtp_fatal), 1 issue e retorna False."""
    email_cliente = "fatal.cliente@exemplo.com"
    provider = _criar_provider(tmp_path)

    with patch(
        "src.ports.smtp_email_provider.EmailMessage",
        side_effect=RuntimeError(f"Erro MIME fatal para {email_cliente}"),
    ):
        resultado = provider.send_email_message(
            email_cliente,
            "Assunto",
            "<p>Corpo</p>",
            plain_text="Corpo",
            is_promotional=False,
        )

    flush_telemetry(timeout=2.0)

    assert resultado is False
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)) == 1
    assert len(sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)) == 0

    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)
    assert len(failed) == 1
    assert _attr_val(failed[0], "email.failure_stage") == "smtp_fatal"
    assert _attr_val(failed[0], "email.error_type") == "RuntimeError"

    eventos = sentry_dummy_transport.events()
    assert len(eventos) == 1
    assert eventos[0]["tags"]["email.failure_stage"] == "smtp_fatal"
    assert len(eventos[0]["exception"]["values"][0]["stacktrace"]["frames"]) >= 1
    assert email_cliente not in sentry_dummy_transport.serialized_payloads().lower()


# ------------------------------------------------------------------------------
# Cenário 8: NotificationService (enriquecimento pedido/carrinho, builder fail, duplicata, DryRun)
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_notification_service_enriquece_pedido_carrinho_e_duplicata(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    sentry_dummy_transport,
    monkeypatch,
):
    """NotificationService enriquece métricas de pedido/carrinho e separa primary vs duplicate."""
    srv = MagicMock()
    srv.noop.return_value = (250, b"OK")
    srv.sendmail.return_value = {}
    mock_smtp_ssl.return_value = srv

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    # 1. Pedido com metadata cart_id
    evento_pedido = _criar_evento_pedido(order_id="801", order_number="PED-801", stg=2, cart_id="CART-801")
    assert service.handle_transition(evento_pedido, "pedido_aprovado") is True

    # 2. Carrinho abandonado com envio duplicado habilitado
    monkeypatch.setattr(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", True)
    evento_carrinho = _criar_evento_carrinho(cart_id="CART-802", stc=15, email="comprador@dominio-cliente.com")
    assert service.handle_cart_transition(evento_carrinho, "carrinho_abandonado_cupom4") is True

    flush_telemetry(timeout=2.0)

    sent = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_SENT)
    assert len(sent) == 3

    # Pedido primário
    m_pedido = sent[0]
    assert _attr_val(m_pedido, "email.flow") == "order"
    assert _attr_val(m_pedido, "email.stage") == "STG_2"
    assert _attr_val(m_pedido, "email.entity_type") == "order"
    assert _attr_val(m_pedido, "email.entity_id") == "801"
    assert _attr_val(m_pedido, "email.order_number") == "PED-801"
    assert _attr_val(m_pedido, "email.cart_id") == "CART-801"
    assert _attr_val(m_pedido, "email.dispatch_kind") == "primary"
    assert _attr_val(m_pedido, "email.recipient_domain") == "exemplo.com"

    # Carrinho primário + duplicata
    m_cart_prim = sent[1]
    assert _attr_val(m_cart_prim, "email.flow") == "abandoned_cart"
    assert _attr_val(m_cart_prim, "email.stage") == "STC_15"
    assert _attr_val(m_cart_prim, "email.entity_type") == "cart"
    assert _attr_val(m_cart_prim, "email.entity_id") == "CART-802"
    assert _attr_val(m_cart_prim, "email.cart_id") == "CART-802"
    assert _attr_val(m_cart_prim, "email.dispatch_kind") == "primary"
    assert _attr_val(m_cart_prim, "email.recipient_domain") == "dominio-cliente.com"

    m_cart_dup = sent[2]
    assert _attr_val(m_cart_dup, "email.dispatch_kind") == "duplicate"
    assert _attr_val(m_cart_dup, "email.recipient_domain") == "elevemeloja.com.br"


def test_notification_service_falha_no_builder_emite_template_build_e_issue(
    tmp_path,
    sentry_dummy_transport,
):
    """Exceção em builder.build_with_plain_text emite started + failed(template_build) + 1 issue."""
    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    email_cliente = "template.erro@exemplo.com"
    evento_pedido = _criar_evento_pedido(order_id="901", order_number="PED-901", email=email_cliente, cart_id=None)

    with patch(
        "src.services.notification_service.PaymentConfirmedBuilder.build_with_plain_text",
        side_effect=ValueError(f"Erro ao renderizar template para {email_cliente}"),
    ):
        assert service.handle_transition(evento_pedido, "pedido_aprovado") is False

    evento_carrinho = _criar_evento_carrinho(cart_id="CART-902", email=email_cliente)
    with patch(
        "src.services.notification_service.Coupon4CartBuilder.build_with_plain_text",
        side_effect=KeyError("chave_ausente"),
    ):
        assert service.handle_cart_transition(evento_carrinho, "carrinho_abandonado_cupom4") is False

    flush_telemetry(timeout=2.0)

    started = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_STARTED)
    failed = sentry_dummy_transport.metrics_by_name(METRIC_EMAIL_DISPATCH_FAILED)
    eventos = sentry_dummy_transport.events()

    assert len(started) == 2
    assert len(failed) == 2
    assert len(eventos) == 2

    for f in failed:
        assert _attr_val(f, "email.failure_stage") == "template_build"
        assert _attr_val(f, "email.provider") == "template_builder"

    assert eventos[0]["tags"]["email.failure_stage"] == "template_build"
    assert len(eventos[0]["exception"]["values"][0]["stacktrace"]["frames"]) >= 1
    payload_serializado = sentry_dummy_transport.serialized_payloads()
    assert email_cliente not in payload_serializado.lower()
    assert "maria silva" not in payload_serializado.lower()
    assert "joão souza" not in payload_serializado.lower()


def test_notification_service_falha_builder_em_homologacao_nao_vaza_cpf_nome_ou_email_real(
    tmp_path,
    sentry_dummy_transport,
    monkeypatch,
):
    """Mesmo com MACRO_FORCE_TEST_EMAIL_RECIPIENT=True, falha no builder não vaza PII do cliente."""
    monkeypatch.setattr(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", True)
    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    email_real = "cliente.cpf.real@exemplo.com"
    evento = OrderTransitionEvent(
        order_id="955",
        order_number="PED-955",
        new_stg=2,
        customer_data={
            "name": "Fernanda Completo LGPD",
            "cpf": "98765432100",
            "email": email_real,
        },
        order_data={"id": "955", "items": {"data": []}},
    )

    with patch(
        "src.services.notification_service.PaymentConfirmedBuilder.build_with_plain_text",
        side_effect=ValueError(f"Erro builder para {email_real} e {config.TEST_EMAIL_RECIPIENT}"),
    ):
        assert service.handle_transition(evento, "pedido_aprovado") is False

    flush_telemetry(timeout=2.0)

    eventos = sentry_dummy_transport.events()
    assert len(eventos) == 1
    serializado = sentry_dummy_transport.serialized_payloads()
    assert email_real not in serializado.lower()
    assert config.TEST_EMAIL_RECIPIENT not in serializado.lower()
    assert "fernanda completo lgpd" not in serializado.lower()
    assert "98765432100" not in serializado


def test_telemetry_edge_cases_e_lgpd_sem_raw_email(sentry_dummy_transport, monkeypatch):
    """Cobre bordas de extract_smtp_error_details, sanitize e capture_email_dispatch_error com raw_email=None."""
    import src.core.telemetry as tel_mod

    assert extract_smtp_error_details(smtplib.SMTPRecipientsRefused({})) == {}
    assert extract_smtp_error_details(smtplib.SMTPRecipientsRefused({"a@b.com": ("bad",)})) == {}
    assert extract_smtp_error_details(
        smtplib.SMTPRecipientsRefused({"a@b.com": ("nao_int", "Falha a@b.com")})
    ) == {"smtp_error": "Falha ***@***"}

    # _sanitize_nested_value preservando tuplas e sanitizando chaves/valores
    res_nested = tel_mod._sanitize_nested_value(
        ("cli@x.com", {"cli@x.com": ["CLI@X.COM", 42]}),
        raw_email="cli@x.com",
        masked_email="c*i@x.com",
    )
    assert res_nested == ("c*i@x.com", {"c*i@x.com": ["c*i@x.com", 42]})

    # capture_email_dispatch_error com raw_email=None ainda redige HTML e password em frame["vars"]
    def _funcao_com_variaveis_sensiveis():
        html_body = "<" + "html><body>" + "Seg" + "redo HTML</body></html>"
        smtp_password = "seg" + "redo_smtp_nao_vazar"
        raise RuntimeError("Falha interna sem raw_email")

    try:
        _funcao_com_variaveis_sensiveis()
    except RuntimeError as exc:
        capture_email_dispatch_error(exc, failure_stage="smtp_fatal", raw_email=None)

    flush_telemetry(timeout=2.0)
    eventos_edge = sentry_dummy_transport.events()
    assert len(eventos_edge) == 1
    frames_edge = eventos_edge[0]["exception"]["values"][0]["stacktrace"]["frames"]
    vars_func = [f["vars"] for f in frames_edge if f.get("function") == "_funcao_com_variaveis_sensiveis"][0]
    assert vars_func["html_body"] == "[REDACTED]"
    assert vars_func["smtp_password"] == "[REDACTED]"
    serializado = sentry_dummy_transport.serialized_payloads()
    assert "segredo html" not in serializado.lower()
    assert "segredo_smtp_nao_vazar" not in serializado

    # Quando sentry_sdk is None, helpers permanecem Zero-Crash e context managers propagam exceções
    monkeypatch.setattr(tel_mod, "sentry_sdk", None)
    add_smtp_retry_breadcrumb(
        attempt=1,
        max_retries=3,
        error_type="OSError",
        smtp_code=None,
        channel="transactional",
        recipient_domain="exemplo.com",
    )
    record_email_dispatch_started({"email.provider": "smtp"})
    capture_email_dispatch_error(RuntimeError("x"), failure_stage="smtp_fatal")
    flush_telemetry(timeout=1.0)
    with pytest.raises(RuntimeError, match="propaga_sem_sdk"):
        with email_dispatch_scope(
            flow="order",
            template_name="pedido_aprovado",
            stage="STG_2",
            entity_type="order",
            entity_id="1",
            is_promotional=False,
        ):
            raise RuntimeError("propaga_sem_sdk")
    with pytest.raises(ValueError, match="span_sem_sdk"):
        with start_smtp_span("SMTP"):
            raise ValueError("span_sem_sdk")


def test_dry_run_provider_nao_emite_metricas_email_dispatch(sentry_dummy_transport):
    """DryRunMessageProvider executado via NotificationService NÃO emite métricas email.dispatch.*."""
    config = _criar_config_teste()
    service = NotificationService(DryRunMessageProvider(), config)

    assert service.handle_transition(_criar_evento_pedido(), "pedido_aprovado") is True
    assert service.handle_cart_transition(_criar_evento_carrinho(), "carrinho_abandonado_cupom4") is True

    flush_telemetry(timeout=2.0)
    assert sentry_dummy_transport.metrics() == []
    assert sentry_dummy_transport.events() == []


# ------------------------------------------------------------------------------
# Cenário 9: Zero-Crash e propagação de exceções de negócio em context managers
# ------------------------------------------------------------------------------


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_zero_crash_sem_sentry_dsn_e_com_falhas_no_sdk(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    monkeypatch,
):
    """Sem DSN ou com falhas no sentry_sdk em runtime, o provedor funciona sem quebrar."""
    srv = MagicMock()
    srv.noop.return_value = (250, b"OK")
    srv.sendmail.return_value = {}
    mock_smtp_ssl.return_value = srv

    global_scope = sentry_sdk.get_global_scope()
    prev_client = global_scope.client
    global_scope.set_client(NonRecordingClient())
    try:
        provider = _criar_provider(tmp_path)
        assert provider.send_email_message("cli@exemplo.com", "Ok", "<p>Ok</p>") is True

        # Simula falhas internas no sentry_sdk durante execução normal e com falha SMTP
        monkeypatch.setattr(sentry_sdk.metrics, "count", MagicMock(side_effect=RuntimeError("Falha metrics")))
        monkeypatch.setattr(sentry_sdk, "capture_exception", MagicMock(side_effect=RuntimeError("Falha capture")))
        monkeypatch.setattr(sentry_sdk, "add_breadcrumb", MagicMock(side_effect=RuntimeError("Falha breadcrumb")))
        monkeypatch.setattr(sentry_sdk, "flush", MagicMock(side_effect=RuntimeError("Falha flush")))

        assert provider.send_email_message("cli@exemplo.com", "Ok 2", "<p>Ok 2</p>") is True

        srv.sendmail.side_effect = smtplib.SMTPServerDisconnected("Queda")
        assert provider.send_email_message("cli@exemplo.com", "Falha", "<p>Falha</p>") is False
        flush_telemetry(timeout=1.0)
    finally:
        global_scope.set_client(prev_client)


def test_context_managers_propagam_excecoes_de_negocio(monkeypatch):
    """email_dispatch_scope e start_smtp_span NUNCA engolem exceções lançadas dentro do bloco."""
    with pytest.raises(ValueError, match="erro_interno_scope"):
        with email_dispatch_scope(
            flow="order",
            template_name="pedido_aprovado",
            stage="STG_2",
            entity_type="order",
            entity_id="1",
            is_promotional=False,
        ):
            raise ValueError("erro_interno_scope")

    with pytest.raises(RuntimeError, match="erro_interno_span"):
        with start_smtp_span("SMTP sendmail (transactional)", data={"smtp.host": "h", "ignorar": None}):
            raise RuntimeError("erro_interno_span")

    # Mesmo quando new_scope ou start_span quebram na abertura, o fallback executa e propaga erro do bloco
    monkeypatch.setattr(sentry_sdk, "new_scope", MagicMock(side_effect=RuntimeError("Falha new_scope")))
    monkeypatch.setattr(sentry_sdk, "start_span", MagicMock(side_effect=RuntimeError("Falha start_span")))

    with pytest.raises(KeyError, match="erro_negocio_com_sdk_quebrado"):
        with email_dispatch_scope(
            flow="order",
            template_name="pedido_aprovado",
            stage="STG_2",
            entity_type="order",
            entity_id="2",
            is_promotional=False,
        ):
            raise KeyError("erro_negocio_com_sdk_quebrado")

    with pytest.raises(ZeroDivisionError):
        with start_smtp_span("SMTP sendmail (promotional)"):
            _ = 1 / 0


# ------------------------------------------------------------------------------
# Cenário 10: main._close_resources() aciona flush_telemetry()
# ------------------------------------------------------------------------------


def test_main_close_resources_chama_flush_telemetry():
    """Garante que _close_resources chama flush_telemetry() e tolera falha no flush."""
    mock_repo = MagicMock()
    mock_provider = MagicMock()

    with patch.object(app_main, "flush_telemetry") as mock_flush:
        app_main._close_resources(mock_repo, mock_provider)
        mock_repo.close.assert_called_once()
        mock_provider.close.assert_called_once()
        mock_flush.assert_called_once()

    with patch.object(app_main, "flush_telemetry", side_effect=RuntimeError("Erro flush")):
        app_main._close_resources(mock_repo, mock_provider)
