from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

from src.core import logging_config, macros
from src.core.client import YampiClient
from src.core.config import Config, load_config
from src.core.time_utils import to_local_sp
from src.domain.events import CartTransitionEvent, OrderTransitionEvent
from src.ports.message_provider import DryRunMessageProvider
from src.services.email_builders.concrete_builders import (
    Coupon4CartBuilder,
    Coupon5CartBuilder,
    Coupon6CartBuilder,
    Coupon10Builder,
    Coupon15Builder,
    Coupon20Builder,
    PaymentConfirmedBuilder,
    PaymentIncentiveBuilder,
    ShippingTrackerBuilder,
)
from src.services.notification_service import NotificationService
import src.main as app_main


def test_run_all_and_individual_runners_close_resources_in_finally():
    """Garante que run_all, run_orders e run_abandoned_carts sempre fecham state_repo e message_provider."""
    mock_config = MagicMock(spec=Config)
    mock_api = MagicMock()
    mock_repo = MagicMock()
    mock_provider = MagicMock()

    with patch.object(app_main, "get_dependencies", return_value=(mock_config, mock_api, mock_repo, mock_provider)), \
         patch.object(app_main, "OrderProcessor") as mock_order_proc, \
         patch.object(app_main, "AbandonedCartProcessor") as mock_cart_proc:

        app_main.run_all()
        app_main.run_orders()
        app_main.run_abandoned_carts()

        assert mock_repo.close.call_count == 3
        assert mock_provider.close.call_count == 3

        # Mesmo quando um processor lança exceção, os recursos devem ser fechados
        mock_repo.reset_mock()
        mock_provider.reset_mock()
        mock_order_proc.return_value.process.side_effect = RuntimeError("Falha simulada no worker")

        with pytest.raises(RuntimeError, match="Falha simulada no worker"):
            app_main.run_all()

        mock_repo.close.assert_called_once()
        mock_provider.close.assert_called_once()


def test_setup_logging_sentry_init_is_idempotent(monkeypatch, tmp_path):
    """Garante que múltiplas chamadas a setup_logging inicializam o Sentry SDK apenas uma vez."""
    monkeypatch.setenv("SENTRY_DSN", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setenv("TRACES_SAMPLE_RATE", "0.5")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setattr(logging_config, "_SENTRY_INITIALIZED", False)

    log_path = str(tmp_path / "test_app.log")
    emails_path = str(tmp_path / "emails")
    with patch("sentry_sdk.init") as mock_sentry_init:
        logging_config.setup_logging(verbose=True, log_file=log_path, emails_dir=emails_path)
        logging_config.setup_logging(verbose=False, log_file=log_path, emails_dir=emails_path)

        mock_sentry_init.assert_called_once_with(
            dsn="https://public@example.ingest.sentry.io/1",
            traces_sample_rate=0.5,
            environment="test",
            send_default_pii=False,
        )


def test_global_exception_hooks_capture_to_sentry(tmp_path):
    """Valida que sys.excepthook e threading.excepthook encaminham exceções não tratadas ao Sentry."""
    import sys
    import threading

    log_path = str(tmp_path / "hooks.log")
    emails_path = str(tmp_path / "emails")
    logging_config.setup_logging(verbose=False, log_file=log_path, emails_dir=emails_path)

    with patch("sentry_sdk.capture_exception") as mock_capture:
        try:
            raise ValueError("Erro fatal simulado")
        except ValueError:
            exc_type, exc_val, exc_tb = sys.exc_info()
            sys.excepthook(exc_type, exc_val, exc_tb)
            threading.excepthook(SimpleNamespace(exc_type=exc_type, exc_value=exc_val, exc_traceback=exc_tb, thread=SimpleNamespace(name="T1")))

        assert mock_capture.call_count == 2


@patch("src.core.client.time.sleep", return_value=None)
@patch("requests.request")
def test_yampi_client_pagination_429_and_merchant_alias(mock_request, mock_sleep):
    """Testa descoberta de merchant_alias via auth/me, retry em HTTP 429 e paginação em múltiplas páginas."""
    client = YampiClient(user_token="tok", user_secret_key="sec", merchant_alias=None)

    resp_auth = MagicMock(status_code=200)
    resp_auth.json.return_value = {
        "data": {"merchants": {"data": [{"active": False, "alias": "inativa"}, {"active": True, "alias": "loja_ativa", "name": "Eleveme"}]}}
    }

    resp_429 = MagicMock(status_code=429, headers={"X-RateLimit-Limit": "100", "X-RateLimit-Remaining": "0"})
    resp_p1 = MagicMock(status_code=200)
    resp_p1.json.return_value = {"data": [{"id": 1}], "meta": {"pagination": {"current_page": 1, "total_pages": 2}}}
    resp_p2 = MagicMock(status_code=200)
    resp_p2.json.return_value = {"data": [{"id": 2}], "meta": {"pagination": {"current_page": 2, "total_pages": 2}}}

    mock_request.side_effect = [resp_auth, resp_429, resp_p1, resp_p2]

    orders = list(client.get_orders(include=["customer", "shipments"]))
    assert [o["id"] for o in orders] == [1, 2]
    assert client.merchant_alias == "loja_ativa"
    assert mock_sleep.call_count == 1

    # Testa também chamadas de get_abandoned_carts e get_products
    resp_single = MagicMock(status_code=200)
    resp_single.json.return_value = {"data": [{"id": 99}], "meta": {"pagination": {"current_page": 1, "total_pages": 1}}}
    mock_request.side_effect = [resp_single, resp_single]

    assert list(client.get_abandoned_carts(include=["customer"])) == [{"id": 99}]
    assert list(client.get_products(include=["skus"])) == [{"id": 99}]


def test_all_concrete_email_builders_and_notification_service():
    """Exercita todos os builders concretos (pedidos e carrinhos) e o NotificationService."""
    config = Config(
        YAMPI_USER_TOKEN="t",
        YAMPI_USER_SECRET_KEY="s",
        YAMPI_ALIAS="alias",
        TEST_EMAIL_RECIPIENT="monitor@eleveme.com",
    )
    customer = {"name": "Maria Silva", "email": "maria@exemplo.com"}
    order_data = {
        "value_total": 150.0,
        "value_shipment": 15.0,
        "value_discount": 10.0,
        "checkout_url": "https://loja.com/pay",
        "shipments": {"data": [{"tracking_code": "BR111222333BR", "tracking_url": "https://rastreio.com"}]},
        "pix": {"data": {"pix_qr_code": "000201PIXCODE"}},
        "items": {"data": [{"item_sku": "SKU-1", "title": "Palmilha", "price": 150.0, "quantity": 1}]},
    }
    cart_data = {
        "value_total": 250.0,
        "simulate_url": "https://loja.com/cart/abc",
        "items": {"data": [{"item_sku": "SKU-2", "title": "Palmilha Pro", "price": 250.0, "quantity": 1}]},
    }

    order_event = OrderTransitionEvent("1", "1001", 2, customer, order_data)
    cart_event = CartTransitionEvent("c-1", 15, customer, cart_data)

    for builder in [
        PaymentConfirmedBuilder(),
        PaymentIncentiveBuilder(),
        ShippingTrackerBuilder(),
        Coupon10Builder(),
        Coupon15Builder(),
        Coupon20Builder(),
    ]:
        subject, html = builder.build(order_event)
        assert subject
        assert "<html" in html.lower()

    for builder in [Coupon4CartBuilder(), Coupon5CartBuilder(), Coupon6CartBuilder()]:
        subject, html = builder.build(cart_event)
        assert subject
        assert "https://loja.com/cart/abc" in html

    dry_provider = DryRunMessageProvider()
    service = NotificationService(dry_provider, config)

    assert service.handle_transition(order_event, "pedido_pendente") is True
    assert service.handle_transition(order_event, "template_inexistente") is False
    assert service.handle_cart_transition(cart_event, "carrinho_abandonado_cupom5") is True
    assert service.handle_cart_transition(cart_event, "template_inexistente") is False

    # Sem e-mail do cliente em modo produção real deve retornar False
    with patch.object(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", False):
        event_sem_email = OrderTransitionEvent("2", "1002", 1, {"name": "Sem Email"}, order_data)
        cart_sem_email = CartTransitionEvent("c-2", 15, {"name": "Sem Email"}, cart_data)
        assert service.handle_transition(event_sem_email, "pedido_aprovado") is False
        assert service.handle_cart_transition(cart_sem_email, "carrinho_abandonado_cupom4") is False


def test_load_config_and_to_local_sp(monkeypatch):
    """Testa carregamento de configuração via env e conversão UTC -> America/Sao_Paulo."""
    monkeypatch.setenv("YAMPI_USER_TOKEN", "tok-env")
    monkeypatch.setenv("YAMPI_USER_SECRET_KEY", "sec-env")
    cfg = load_config()
    assert cfg.YAMPI_USER_TOKEN == "tok-env"

    monkeypatch.delenv("YAMPI_USER_TOKEN", raising=False)
    with pytest.raises(ValueError):
        load_config()

    dt_naive = datetime(2026, 8, 10, 3, 0, 0)
    dt_sp = to_local_sp(dt_naive)
    assert dt_sp.hour == 0
    assert dt_sp.tzinfo is not None


def test_daemon_main_executes_cycle_with_sentry_cron_and_handles_exception():
    """Testa o ciclo principal do daemon com Sentry Crons, tratamento de exceção e encerramento no sleep."""
    import src.daemon as daemon_mod

    with patch.object(daemon_mod, "run_all", side_effect=[None, RuntimeError("Erro de ciclo")]) as mock_run_all, \
         patch.object(daemon_mod.time, "sleep", side_effect=[None, KeyboardInterrupt()]) as mock_sleep, \
         patch.object(daemon_mod.sentry_sdk.crons, "monitor") as mock_monitor:
        mock_monitor.return_value.__enter__.return_value = None
        mock_monitor.return_value.__exit__.return_value = False

        with pytest.raises(KeyboardInterrupt):
            daemon_mod.main()

        assert mock_run_all.call_count == 2
        assert mock_monitor.call_count == 2
        assert mock_sleep.call_count == 2


def test_main_get_dependencies_dry_run_and_production(monkeypatch):
    """Testa injeção de dependências em modo dry-run, produção e erro de SMTP ausente."""
    monkeypatch.setenv("YAMPI_USER_TOKEN", "tok")
    monkeypatch.setenv("YAMPI_USER_SECRET_KEY", "sec")
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    with patch.object(app_main, "PostgresStateRepository") as mock_repo_cls:
        with patch.object(macros, "MACRO_ENABLE_REAL_EMAIL_DISPATCH", False):
            _, _, _, provider = app_main.get_dependencies()
            assert isinstance(provider, DryRunMessageProvider)

        with patch.object(macros, "MACRO_ENABLE_REAL_EMAIL_DISPATCH", True):
            with pytest.raises(SystemExit) as exc_info:
                app_main.get_dependencies()
            assert exc_info.value.code == 1

            monkeypatch.setenv("SMTP_USER", "smtp@eleveme.com")
            monkeypatch.setenv("SMTP_PASSWORD", "senha123")
            _, _, _, prod_provider = app_main.get_dependencies()
            assert prod_provider.user == "smtp@eleveme.com"
        assert mock_repo_cls.call_count == 3


def test_notification_service_duplicate_test_mode_and_local_html(tmp_path, monkeypatch):
    """Testa envio duplicado de supervisão, modo homologação, falha no provedor e salvamento HTML local."""
    monkeypatch.chdir(tmp_path)
    config = Config(
        YAMPI_USER_TOKEN="t",
        YAMPI_USER_SECRET_KEY="s",
        YAMPI_ALIAS="alias",
        TEST_EMAIL_RECIPIENT="monitor@eleveme.com",
    )
    customer = {"name": "João", "email": "joao@exemplo.com"}
    order_data = {"value_total": 90.0, "items": {"data": [{"item_sku": "S1", "title": "Item", "price": 90.0, "quantity": 1}]}}
    cart_data = {"value_total": 90.0, "simulate_url": "https://loja.com/c", "items": {"data": [{"item_sku": "S1", "title": "Item", "price": 90.0, "quantity": 1}]}}
    order_event = OrderTransitionEvent("10", "2000", 1, customer, order_data)
    cart_event = CartTransitionEvent("c-10", 15, customer, cart_data)

    mock_provider = MagicMock()
    mock_provider.send_email_message.return_value = True
    service = NotificationService(mock_provider, config)

    with patch.object(macros, "MACRO_ENABLE_LOCAL_HTML_SAVING", True), \
         patch.object(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", False), \
         patch.object(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", True):
        assert service.handle_transition(order_event, "pedido_aprovado") is True
        assert service.handle_cart_transition(cart_event, "carrinho_abandonado_cupom4") is True
        assert mock_provider.send_email_message.call_count == 4

    with patch.object(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", True):
        mock_provider.send_email_message.return_value = False
        assert service.handle_cart_transition(cart_event, "carrinho_abandonado_cupom4") is False


def test_yampi_client_4xx_error_and_fallback_merchant():
    """Testa erro 4xx sem retry e fallback para primeira loja inativa em _fetch_merchant_alias."""
    import requests as req_lib

    client = YampiClient(user_token="tok", user_secret_key="sec", merchant_alias=None)
    resp_auth_inativa = MagicMock(status_code=200)
    resp_auth_inativa.json.return_value = {
        "data": {"merchants": {"data": [{"active": False, "alias": "loja_fallback", "name": "Fallback"}]}}
    }
    resp_401 = MagicMock(status_code=401)
    resp_401.raise_for_status.side_effect = req_lib.exceptions.HTTPError("401 Unauthorized")

    with patch("requests.request", side_effect=[resp_auth_inativa, resp_401]):
        assert client.merchant_alias == "loja_fallback"
        with pytest.raises(req_lib.exceptions.HTTPError):
            client.request("GET", "orders")


def test_webhook_server_routes():
    """Testa validação GET e recebimento POST (mensagens, status e erro) no Flask webhook_server."""
    import src.webhook_server as ws

    client = ws.app.test_client()

    # GET válido e inválido
    resp_ok = client.get(f"/webhook?hub.mode=subscribe&hub.verify_token={ws.VERIFY_TOKEN}&hub.challenge=CHALLENGE_OK")
    assert resp_ok.status_code == 200
    assert resp_ok.get_data(as_text=True) == "CHALLENGE_OK"

    resp_forbidden = client.get("/webhook?hub.mode=subscribe&hub.verify_token=errado&hub.challenge=123")
    assert resp_forbidden.status_code == 403

    # POST mensagem, status e payload inesperado
    resp_msg = client.post("/webhook", json={"entry": [{"changes": [{"value": {"messages": [{"from": "5511", "text": {"body": "Oi"}}]}}]}]})
    assert resp_msg.status_code == 200

    resp_status = client.post("/webhook", json={"entry": [{"changes": [{"value": {"statuses": [{"recipient_id": "5511", "status": "delivered"}]}}]}]})
    assert resp_status.status_code == 200

    resp_err = client.post("/webhook", json={"entry": None})
    assert resp_err.status_code == 200


def test_record_daemon_cycle_metrics_emite_count_e_distribution():
    """Garante que record_daemon_cycle_metrics emite count e distribution com atributos esperados."""
    from src.core import telemetry

    mock_metrics = MagicMock()
    mock_sentry = SimpleNamespace(metrics=mock_metrics)

    with patch.object(telemetry, "sentry_sdk", mock_sentry):
        telemetry.record_daemon_cycle_metrics(status="ok", duration_seconds=1.75)
        telemetry.record_daemon_cycle_metrics(
            status="error",
            duration_seconds=0.5,
            monitor_slug="custom-daemon-slug",
        )

    mock_metrics.count.assert_any_call(
        "daemon.cycle.completed",
        1,
        attributes={"monitor.slug": "yampi-daemon-cycle", "status": "ok"},
    )
    mock_metrics.distribution.assert_any_call(
        "daemon.cycle.duration",
        1.75,
        unit="second",
        attributes={"monitor.slug": "yampi-daemon-cycle", "status": "ok"},
    )
    mock_metrics.count.assert_any_call(
        "daemon.cycle.completed",
        1,
        attributes={"monitor.slug": "custom-daemon-slug", "status": "error"},
    )
    mock_metrics.distribution.assert_any_call(
        "daemon.cycle.duration",
        0.5,
        unit="second",
        attributes={"monitor.slug": "custom-daemon-slug", "status": "error"},
    )


def test_record_daemon_cycle_metrics_respeita_zero_crash_e_normaliza_duracao_negativa():
    """Garante política Zero-Crash em falhas do Sentry SDK/ausência de métricas e clamp de duração negativa para 0.0."""
    from src.core import telemetry

    # Sem sentry_sdk disponível
    with patch.object(telemetry, "sentry_sdk", None):
        telemetry.record_daemon_cycle_metrics(status="ok", duration_seconds=2.0)

    # sentry_sdk sem atributo metrics
    with patch.object(telemetry, "sentry_sdk", SimpleNamespace()):
        telemetry.record_daemon_cycle_metrics(status="ok", duration_seconds=2.0)

    # Falha em metrics.count não deve propagar exceção
    mock_metrics_erro_count = MagicMock()
    mock_metrics_erro_count.count.side_effect = RuntimeError("falha simulada no count")
    with patch.object(telemetry, "sentry_sdk", SimpleNamespace(metrics=mock_metrics_erro_count)):
        telemetry.record_daemon_cycle_metrics(status="error", duration_seconds=1.0)

    # Falha em metrics.distribution não deve propagar exceção
    mock_metrics_erro_dist = MagicMock()
    mock_metrics_erro_dist.distribution.side_effect = RuntimeError("falha simulada no distribution")
    with patch.object(telemetry, "sentry_sdk", SimpleNamespace(metrics=mock_metrics_erro_dist)):
        telemetry.record_daemon_cycle_metrics(status="ok", duration_seconds=1.0)

    # Duração negativa deve ser normalizada para 0.0
    mock_metrics_neg = MagicMock()
    with patch.object(telemetry, "sentry_sdk", SimpleNamespace(metrics=mock_metrics_neg)):
        telemetry.record_daemon_cycle_metrics(status="ok", duration_seconds=-3.5)

    mock_metrics_neg.distribution.assert_called_once_with(
        "daemon.cycle.duration",
        0.0,
        unit="second",
        attributes={"monitor.slug": "yampi-daemon-cycle", "status": "ok"},
    )


def test_daemon_main_registra_metricas_ok_e_error_com_flush_telemetry():
    """Valida que daemon.main() registra métricas com status='ok' e status='error' + flush_telemetry em falha."""
    import src.daemon as daemon_mod

    fake_time = SimpleNamespace(
        perf_counter=MagicMock(side_effect=[10.0, 12.5, 20.0, 21.25]),
        sleep=MagicMock(side_effect=[None, KeyboardInterrupt()]),
    )

    with patch.object(daemon_mod, "run_all", side_effect=[None, RuntimeError("Erro de ciclo")]) as mock_run_all, \
         patch.object(daemon_mod, "time", fake_time), \
         patch.object(daemon_mod.sentry_sdk.crons, "monitor") as mock_monitor, \
         patch.object(daemon_mod, "record_daemon_cycle_metrics") as mock_record_metrics, \
         patch.object(daemon_mod, "flush_telemetry") as mock_flush:
        mock_monitor.return_value.__enter__.return_value = None
        mock_monitor.return_value.__exit__.return_value = False

        with pytest.raises(KeyboardInterrupt):
            daemon_mod.main()

    assert mock_run_all.call_count == 2
    assert mock_record_metrics.call_count == 2
    assert mock_record_metrics.call_args_list[0].kwargs == {
        "status": "ok",
        "duration_seconds": pytest.approx(2.5),
        "monitor_slug": macros.MACRO_SENTRY_CRON_MONITOR_SLUG,
    }
    assert mock_record_metrics.call_args_list[1].kwargs == {
        "status": "error",
        "duration_seconds": pytest.approx(1.25),
        "monitor_slug": macros.MACRO_SENTRY_CRON_MONITOR_SLUG,
    }
    mock_flush.assert_called_once_with()


def test_core_readme_documenta_metricas_daemon_sem_links_locais():
    """Garante que src/core/README.md documenta as métricas do daemon e não contém file:// nem /home/."""
    from pathlib import Path

    readme_path = Path(__file__).resolve().parent.parent / "src" / "core" / "README.md"
    conteudo = readme_path.read_text(encoding="utf-8")

    assert "METRIC_DAEMON_CYCLE_COMPLETED" in conteudo
    assert "METRIC_DAEMON_CYCLE_DURATION" in conteudo
    assert "record_daemon_cycle_metrics" in conteudo
    assert "file://" not in conteudo
    assert "/home/" not in conteudo

