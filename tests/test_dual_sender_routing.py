"""Testes ponta a ponta do roteamento dual (NotificationService -> SMTPEmailProvider)."""

from concurrent.futures import ThreadPoolExecutor
import email as email_lib
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from src.core import macros
from src.core.config import Config
from src.domain.events import CartTransitionEvent, OrderTransitionEvent
from src.ports.smtp_email_provider import SMTPEmailProvider
from src.services.notification_service import NotificationService

EMAIL_OFICIAL = "oficial@elevemeloja.com.br"
EMAIL_COMERCIAL = "comercial@elevemeloja.com.br"


def _criar_config_teste() -> Config:
    """Cria uma configuração determinística para os testes de roteamento dual."""
    return Config(
        YAMPI_USER_TOKEN="token-teste",
        YAMPI_USER_SECRET_KEY="secret-teste",
        TEST_EMAIL_RECIPIENT="supervisao@elevemeloja.com.br",
        SMTP_HOST="smtp.elevemeloja.com.br",
        SMTP_PORT=465,
        SMTP_USER=EMAIL_OFICIAL,
        SMTP_PASSWORD="senha-oficial-teste",
        SMTP_FROM=EMAIL_OFICIAL,
        PROMO_SMTP_USER=EMAIL_COMERCIAL,
        PROMO_SMTP_PASSWORD="senha-comercial-teste",
        PROMO_SMTP_FROM=EMAIL_COMERCIAL,
    )


def _criar_provider(tmp_path, **sobrescritas) -> SMTPEmailProvider:
    """Instancia o SMTPEmailProvider apontando assets_dir para tmp_path."""
    parametros = {
        "host": "smtp.elevemeloja.com.br",
        "port": 465,
        "user": EMAIL_OFICIAL,
        "password": "senha-oficial-teste",
        "from_addr": EMAIL_OFICIAL,
        "promo_user": EMAIL_COMERCIAL,
        "promo_password": "senha-comercial-teste",
        "promo_from_addr": EMAIL_COMERCIAL,
        "assets_dir": str(tmp_path),
    }
    parametros.update(sobrescritas)
    return SMTPEmailProvider(**parametros)


def _criar_evento_pedido(order_id: str = "101", stg: int = 2) -> OrderTransitionEvent:
    """Cria um evento de transição de pedido com os campos mínimos necessários."""
    return OrderTransitionEvent(
        order_id=order_id,
        order_number=f"PED-{order_id}",
        new_stg=stg,
        customer_data={
            "name": "Maria Silva",
            "first_name": "Maria",
            "email": "maria.cliente@exemplo.com",
        },
        order_data={
            "id": order_id,
            "number": f"PED-{order_id}",
            "value_total": 199.90,
            "status_url": "https://elevemeloja.com.br/pedido/101",
            "checkout_url": "https://elevemeloja.com.br/checkout/101",
            "tracking_code": "BR123456789XX",
            "tracking_url": "https://rastreio.exemplo.com/BR123456789XX",
            "items": [{"name": "Vestido Floral", "quantity": 1, "price": 199.90}],
        },
    )


def _criar_evento_carrinho(cart_id: str = "202", stc: int = 15) -> CartTransitionEvent:
    """Cria um evento de carrinho abandonado com os campos mínimos necessários."""
    return CartTransitionEvent(
        cart_id=cart_id,
        new_stc=stc,
        customer_data={
            "name": "João Souza",
            "first_name": "João",
            "email": "joao.cliente@exemplo.com",
        },
        cart_data={
            "id": cart_id,
            "checkout_url": "https://elevemeloja.com.br/recuperar/202",
            "value_total": 149.90,
            "items": [{"name": "Blusa Linho", "quantity": 1, "price": 149.90}],
        },
    )


def _criar_fabrica_smtp_por_conta():
    """Retorna uma fábrica de servidores mockados separada por credencial de login."""
    servidores = {
        "oficial": MagicMock(name="server_oficial"),
        "promo": MagicMock(name="server_promo"),
        "outros": [],
    }
    for srv in (servidores["oficial"], servidores["promo"]):
        srv.noop.return_value = (250, b"OK")

    def fabrica_smtp(*args, **kwargs):
        servidor = MagicMock(name="smtp_ssl_conn")
        servidor.noop.return_value = (250, b"OK")

        def registrar_login(user, password):
            if user == EMAIL_OFICIAL:
                servidores["oficial_autenticado"] = servidor
            elif user == EMAIL_COMERCIAL:
                servidores["promo_autenticado"] = servidor
            return (235, b"Authentication successful")

        servidor.login.side_effect = registrar_login
        servidores["outros"].append(servidor)
        return servidor

    return fabrica_smtp, servidores


@pytest.fixture(autouse=True)
def _isolamento_macros(monkeypatch):
    """Garante que macros globais de envio não interfiram nos testes."""
    monkeypatch.setattr(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", False)
    monkeypatch.setattr(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", False)
    monkeypatch.setattr(macros, "MACRO_ENABLE_LOCAL_HTML_SAVING", False)


@pytest.mark.parametrize(
    "template_name, tipo_evento, esperado_promocional",
    [
        ("pedido_aprovado", "pedido", False),
        ("pedido_pendente", "pedido", False),
        ("pedido_a_caminho", "pedido", False),
        ("cupom_pedido_1", "pedido", True),
        ("cupom_pedido_2", "pedido", True),
        ("cupom_pedido_3", "pedido", True),
        ("carrinho_abandonado_cupom4", "carrinho", True),
        ("carrinho_abandonado_cupom5", "carrinho", True),
        ("carrinho_abandonado_cupom6", "carrinho", True),
    ],
)
@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_matriz_completa_9_templates_roteamento_dual(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    template_name,
    tipo_evento,
    esperado_promocional,
):
    """Valida roteamento, remetente, ordem MIME e cabeçalhos para todos os 9 templates."""
    fabrica_smtp, _ = _criar_fabrica_smtp_por_conta()
    mock_smtp_ssl.side_effect = fabrica_smtp

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    if tipo_evento == "pedido":
        sucesso = service.handle_transition(_criar_evento_pedido(), template_name)
    else:
        sucesso = service.handle_cart_transition(_criar_evento_carrinho(), template_name)

    assert sucesso is True
    mock_sleep.assert_called_once()

    if esperado_promocional:
        assert provider._promo_server is not None
        assert provider._server is None
        servidor_ativo = provider._promo_server
        remetente_esperado = EMAIL_COMERCIAL
    else:
        assert provider._server is not None
        assert provider._promo_server is None
        servidor_ativo = provider._server
        remetente_esperado = EMAIL_OFICIAL

    servidor_ativo.login.assert_called_once_with(
        remetente_esperado,
        "senha-comercial-teste" if esperado_promocional else "senha-oficial-teste",
    )
    servidor_ativo.sendmail.assert_called_once()

    envelope_from, destinatarios, raw_msg = servidor_ativo.sendmail.call_args[0]
    email_esperado = "maria.cliente@exemplo.com" if tipo_evento == "pedido" else "joao.cliente@exemplo.com"
    assert envelope_from == remetente_esperado
    assert len(destinatarios) == 1
    assert destinatarios[0] == email_esperado

    msg = email_lib.message_from_string(raw_msg)
    assert msg["To"] == email_esperado
    assert remetente_esperado in msg["From"]
    assert EMAIL_COMERCIAL in msg["Reply-To"]
    assert msg["Message-ID"] is not None
    assert msg["Date"] is not None

    tipos_conteudo = [
        parte.get_content_type()
        for parte in msg.walk()
        if parte.get_content_type() in ("text/plain", "text/html")
    ]
    assert tipos_conteudo == ["text/plain", "text/html"]

    if esperado_promocional:
        assert msg["List-Unsubscribe"] is not None
        assert macros.MACRO_EMAIL_UNSUBSCRIBE_URL in msg["List-Unsubscribe"]
        assert f"mailto:{EMAIL_COMERCIAL}" in msg["List-Unsubscribe"]
        assert msg["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    else:
        assert msg["List-Unsubscribe"] is None
        assert msg["List-Unsubscribe-Post"] is None


@pytest.mark.parametrize(
    "promo_user, promo_password",
    [
        (None, "senha-promo"),
        ("", "senha-promo"),
        (EMAIL_COMERCIAL, None),
        (EMAIL_COMERCIAL, ""),
    ],
)
@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_fallback_seguro_para_server_quando_credencial_promo_ausente(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    promo_user,
    promo_password,
):
    """Se promo_user ou promo_password faltar, usa _server (oficial@) mantendo List-Unsubscribe."""
    fabrica_smtp, _ = _criar_fabrica_smtp_por_conta()
    mock_smtp_ssl.side_effect = fabrica_smtp

    config = _criar_config_teste()
    provider = _criar_provider(
        tmp_path,
        promo_user=promo_user,
        promo_password=promo_password,
        promo_from_addr=EMAIL_COMERCIAL,
    )
    service = NotificationService(provider, config)

    sucesso = service.handle_transition(_criar_evento_pedido(), "cupom_pedido_1")

    assert sucesso is True
    assert provider._server is not None
    assert provider._promo_server is None
    provider._server.login.assert_called_once_with(EMAIL_OFICIAL, "senha-oficial-teste")

    envelope_from, _, raw_msg = provider._server.sendmail.call_args[0]
    assert envelope_from == EMAIL_OFICIAL

    msg = email_lib.message_from_string(raw_msg)
    assert EMAIL_OFICIAL in msg["From"]
    assert msg["List-Unsubscribe"] is not None
    assert f"mailto:{EMAIL_COMERCIAL}" in msg["List-Unsubscribe"]
    assert msg["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


@pytest.mark.parametrize(
    "excecao_smtp",
    [
        smtplib.SMTPAuthenticationError(535, b"5.7.8 Authentication failed"),
        smtplib.SMTPServerDisconnected("Conexao promocional encerrada"),
    ],
)
@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_erro_smtp_canal_promocional_nao_afeta_server_transacional(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    excecao_smtp,
):
    """Falha definitiva no canal promo retorna False, zera _promo_server e preserva _server."""
    servidor_transacional = MagicMock(name="server_transacional")
    servidor_transacional.noop.return_value = (250, b"OK")

    servidor_promo_falho = MagicMock(name="server_promo_falho")
    if isinstance(excecao_smtp, smtplib.SMTPAuthenticationError):
        servidor_promo_falho.login.side_effect = excecao_smtp
    else:
        servidor_promo_falho.sendmail.side_effect = excecao_smtp

    mock_smtp_ssl.side_effect = [
        servidor_transacional,
        servidor_promo_falho,
        servidor_promo_falho,
        servidor_promo_falho,
    ]

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    # 1. Conecta e envia no canal transacional primeiro
    assert service.handle_transition(_criar_evento_pedido("1"), "pedido_aprovado") is True
    assert provider._server is servidor_transacional

    # 2. Canal promocional falha até esgotar MACRO_SMTP_MAX_RETRIES
    assert service.handle_transition(_criar_evento_pedido("2"), "cupom_pedido_2") is False
    assert provider._promo_server is None

    # 3. Canal transacional permanece intacto e operacional
    assert provider._server is servidor_transacional
    assert service.handle_transition(_criar_evento_pedido("3"), "pedido_a_caminho") is True
    assert servidor_transacional.sendmail.call_count == 2
    assert mock_sleep.call_count == 2 + (macros.MACRO_SMTP_MAX_RETRIES - 1)


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_reconexao_promo_apos_queda_transitoria(mock_smtp_ssl, mock_sleep, tmp_path):
    """_promo_server falha na 1a tentativa, reconecta na 2a e retorna True."""
    servidor_promo_1 = MagicMock(name="promo_tentativa_1")
    servidor_promo_1.sendmail.side_effect = smtplib.SMTPServerDisconnected("Queda transitoria")

    servidor_promo_2 = MagicMock(name="promo_tentativa_2")
    servidor_promo_2.noop.return_value = (250, b"OK")

    mock_smtp_ssl.side_effect = [servidor_promo_1, servidor_promo_2]

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    sucesso = service.handle_cart_transition(_criar_evento_carrinho(), "carrinho_abandonado_cupom4")

    assert sucesso is True
    assert provider._promo_server is servidor_promo_2
    assert servidor_promo_1.sendmail.call_count == 1
    assert servidor_promo_2.login.call_count == 1
    assert servidor_promo_2.sendmail.call_count == 1
    # 1 sleep de backoff entre tentativa 1 e 2 + 1 sleep de throttle após sucesso
    assert mock_sleep.call_count == 2


def test_close_parcial_e_fallback_em_excecao_quit(tmp_path):
    """Valida close() com apenas um canal aberto e fallback para close() quando quit() falha."""
    # Cenário 1: somente _server aberto
    provider_so_transacional = _criar_provider(tmp_path)
    srv_oficial = MagicMock()
    provider_so_transacional._server = srv_oficial
    provider_so_transacional.close()
    srv_oficial.quit.assert_called_once()
    assert provider_so_transacional._server is None
    assert provider_so_transacional._promo_server is None

    # Cenário 2: somente _promo_server aberto
    provider_so_promo = _criar_provider(tmp_path)
    srv_promo = MagicMock()
    provider_so_promo._promo_server = srv_promo
    provider_so_promo.close()
    srv_promo.quit.assert_called_once()
    assert provider_so_promo._server is None
    assert provider_so_promo._promo_server is None

    # Cenário 3: ambos abertos, quit() do primeiro falha -> faz fallback para close() e fecha o segundo
    provider_ambos = _criar_provider(tmp_path)
    srv_1 = MagicMock()
    srv_1.quit.side_effect = smtplib.SMTPException("Erro no QUIT")
    srv_2 = MagicMock()
    provider_ambos._server = srv_1
    provider_ambos._promo_server = srv_2

    provider_ambos.close()

    srv_1.quit.assert_called_once()
    srv_1.close.assert_called_once()
    srv_2.quit.assert_called_once()
    assert provider_ambos._server is None
    assert provider_ambos._promo_server is None


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_concorrencia_thread_pool_nao_mistura_contas_ou_from(mock_smtp_ssl, mock_sleep, tmp_path):
    """4 threads enviando avisos e promoções no mesmo provider não misturam From nem conexões."""
    servidores_por_conta = {}

    def fabrica_smtp_concorrente(*args, **kwargs):
        servidor = MagicMock()
        servidor.noop.return_value = (250, b"OK")

        def registrar_login(user, password):
            servidores_por_conta[user] = servidor
            return (235, b"OK")

        servidor.login.side_effect = registrar_login
        return servidor

    mock_smtp_ssl.side_effect = fabrica_smtp_concorrente

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    tarefas = []
    for idx in range(16):
        if idx % 2 == 0:
            tarefas.append(("pedido", idx, "pedido_aprovado"))
        else:
            tarefas.append(("carrinho", idx, "carrinho_abandonado_cupom5"))

    def executar_envio(item):
        tipo, idx, template = item
        if tipo == "pedido":
            return service.handle_transition(_criar_evento_pedido(str(idx)), template)
        return service.handle_cart_transition(_criar_evento_carrinho(str(idx)), template)

    with ThreadPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(executar_envio, tarefas))

    assert all(resultados)
    assert EMAIL_OFICIAL in servidores_por_conta
    assert EMAIL_COMERCIAL in servidores_por_conta
    assert servidores_por_conta[EMAIL_OFICIAL] is not servidores_por_conta[EMAIL_COMERCIAL]

    chamadas_oficial = servidores_por_conta[EMAIL_OFICIAL].sendmail.call_args_list
    chamadas_comercial = servidores_por_conta[EMAIL_COMERCIAL].sendmail.call_args_list
    assert len(chamadas_oficial) == 8
    assert len(chamadas_comercial) == 8

    for call in chamadas_oficial:
        envelope_from, _, raw_msg = call[0]
        msg = email_lib.message_from_string(raw_msg)
        assert envelope_from == EMAIL_OFICIAL
        assert EMAIL_OFICIAL in msg["From"]
        assert msg["List-Unsubscribe"] is None

    for call in chamadas_comercial:
        envelope_from, _, raw_msg = call[0]
        msg = email_lib.message_from_string(raw_msg)
        assert envelope_from == EMAIL_COMERCIAL
        assert EMAIL_COMERCIAL in msg["From"]
        assert msg["List-Unsubscribe"] is not None


@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_template_invalido_retorna_false_sem_chamar_smtp(mock_smtp_ssl, tmp_path):
    """Template desconhecido em pedido ou carrinho retorna False sem abrir conexão SMTP."""
    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    assert service.handle_transition(_criar_evento_pedido(), "template_inexistente") is False
    assert service.handle_cart_transition(_criar_evento_carrinho(), "carrinho_inexistente") is False
    mock_smtp_ssl.assert_not_called()
    assert provider._server is None
    assert provider._promo_server is None


@pytest.mark.parametrize("email_invalido", [None, "", "   "])
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_email_cliente_ausente_ou_vazio_retorna_false_sem_chamar_smtp(
    mock_smtp_ssl,
    tmp_path,
    email_invalido,
):
    """E-mail vazio, só espaços ou None retorna False sem disparar SMTP."""
    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    evento_pedido = _criar_evento_pedido()
    evento_pedido.customer_data["email"] = email_invalido

    evento_carrinho = _criar_evento_carrinho()
    evento_carrinho.customer_data["email"] = email_invalido

    assert service.handle_transition(evento_pedido, "pedido_aprovado") is False
    assert service.handle_cart_transition(evento_carrinho, "carrinho_abandonado_cupom4") is False
    mock_smtp_ssl.assert_not_called()


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_force_test_recipient_e_duplicate_dispatch_preservam_canal_dual(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
    monkeypatch,
):
    """Redirecionamento e duplicata preservam is_promotional e roteamento (_server vs _promo_server)."""
    fabrica_smtp, _ = _criar_fabrica_smtp_por_conta()
    mock_smtp_ssl.side_effect = fabrica_smtp

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    # 1. MACRO_FORCE_TEST_EMAIL_RECIPIENT=True redireciona para TEST_EMAIL_RECIPIENT preservando canal
    monkeypatch.setattr(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", True)
    monkeypatch.setattr(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", False)

    assert service.handle_transition(_criar_evento_pedido("10"), "pedido_aprovado") is True
    assert service.handle_cart_transition(_criar_evento_carrinho("20"), "carrinho_abandonado_cupom4") is True

    assert provider._server.sendmail.call_count == 1
    assert provider._server.sendmail.call_args[0][1] == [config.TEST_EMAIL_RECIPIENT]
    assert provider._promo_server.sendmail.call_count == 1
    assert provider._promo_server.sendmail.call_args[0][1] == [config.TEST_EMAIL_RECIPIENT]

    # 2. MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH=True envia cliente + cópia no mesmo canal e flags
    monkeypatch.setattr(macros, "MACRO_FORCE_TEST_EMAIL_RECIPIENT", False)
    monkeypatch.setattr(macros, "MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH", True)

    assert service.handle_transition(_criar_evento_pedido("11"), "pedido_pendente") is True
    assert service.handle_transition(_criar_evento_pedido("12"), "cupom_pedido_1") is True

    # _server: 1 anterior + 2 do pedido_pendente (cliente + duplicata) = 3
    assert provider._server.sendmail.call_count == 3
    destinos_server = [c[0][1][0] for c in provider._server.sendmail.call_args_list[-2:]]
    assert destinos_server == ["maria.cliente@exemplo.com", config.TEST_EMAIL_RECIPIENT]
    for call in provider._server.sendmail.call_args_list[-2:]:
        msg = email_lib.message_from_string(call[0][2])
        assert EMAIL_OFICIAL in msg["From"]
        assert msg["List-Unsubscribe"] is None

    # _promo_server: 1 anterior + 2 do cupom_pedido_1 (cliente + duplicata) = 3
    assert provider._promo_server.sendmail.call_count == 3
    destinos_promo = [c[0][1][0] for c in provider._promo_server.sendmail.call_args_list[-2:]]
    assert destinos_promo == ["maria.cliente@exemplo.com", config.TEST_EMAIL_RECIPIENT]
    for call in provider._promo_server.sendmail.call_args_list[-2:]:
        msg = email_lib.message_from_string(call[0][2])
        assert EMAIL_COMERCIAL in msg["From"]
        assert msg["List-Unsubscribe"] is not None


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP")
def test_starttls_porta_587_roteamento_dual_promo_server(mock_smtp, mock_sleep, tmp_path):
    """Conexão STARTTLS na porta 587 autentica e envia corretamente via _promo_server."""
    fabrica_smtp, _ = _criar_fabrica_smtp_por_conta()
    mock_smtp.side_effect = fabrica_smtp

    config = _criar_config_teste()
    config.SMTP_PORT = 587
    provider = _criar_provider(tmp_path, port=587)
    service = NotificationService(provider, config)

    assert service.handle_transition(_criar_evento_pedido("5871"), "pedido_aprovado") is True
    assert service.handle_cart_transition(_criar_evento_carrinho("5872"), "carrinho_abandonado_cupom6") is True

    assert provider._server is not None
    assert provider._promo_server is not None
    assert provider._server is not provider._promo_server

    provider._server.starttls.assert_called_once()
    provider._server.login.assert_called_once_with(EMAIL_OFICIAL, "senha-oficial-teste")
    provider._promo_server.starttls.assert_called_once()
    provider._promo_server.login.assert_called_once_with(EMAIL_COMERCIAL, "senha-comercial-teste")

    envelope_promo, _, raw_promo = provider._promo_server.sendmail.call_args[0]
    assert envelope_promo == EMAIL_COMERCIAL
    msg_promo = email_lib.message_from_string(raw_promo)
    assert EMAIL_COMERCIAL in msg_promo["From"]
    assert msg_promo["List-Unsubscribe"] is not None


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_erro_canal_transacional_preserva_promo_e_noop_generico_reconecta(
    mock_smtp_ssl,
    mock_sleep,
    tmp_path,
):
    """Falha no _server preserva _promo_server, e exceção genérica em noop() força reconexão limpa."""
    servidor_promo = MagicMock(name="server_promo_vivo")
    servidor_promo.noop.return_value = (250, b"OK")

    servidor_trans_falho = MagicMock(name="server_trans_falho")
    servidor_trans_falho.sendmail.side_effect = smtplib.SMTPServerDisconnected("Queda transacional")

    servidor_promo_reconectado = MagicMock(name="server_promo_reconectado")
    servidor_promo_reconectado.noop.return_value = (250, b"OK")

    mock_smtp_ssl.side_effect = [
        servidor_promo,
        servidor_trans_falho,
        servidor_trans_falho,
        servidor_trans_falho,
        servidor_promo_reconectado,
    ]

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path)
    service = NotificationService(provider, config)

    # 1. Conecta e envia no canal promocional
    assert service.handle_transition(_criar_evento_pedido("1"), "cupom_pedido_1") is True
    assert provider._promo_server is servidor_promo

    # 2. Canal transacional falha até esgotar retries; _promo_server permanece preservado
    assert service.handle_transition(_criar_evento_pedido("2"), "pedido_aprovado") is False
    assert provider._server is None
    assert provider._promo_server is servidor_promo

    # 3. Exceção genérica em noop() do _promo_server força reconexão limpa na próxima chamada
    servidor_promo.noop.side_effect = RuntimeError("Socket corrompido no noop")
    assert service.handle_cart_transition(_criar_evento_carrinho("3"), "carrinho_abandonado_cupom5") is True
    assert provider._promo_server is servidor_promo_reconectado
    servidor_promo_reconectado.login.assert_called_once_with(EMAIL_COMERCIAL, "senha-comercial-teste")
    servidor_promo_reconectado.sendmail.assert_called_once()


def test_close_falha_dupla_quit_e_close_nao_propaga_excecao(tmp_path):
    """Se quit() e close() falharem em ambos os servidores, não propaga exceção e zera atributos."""
    provider = _criar_provider(tmp_path)
    srv_1 = MagicMock()
    srv_1.quit.side_effect = smtplib.SMTPException("Falha quit 1")
    srv_1.close.side_effect = OSError("Falha close 1")

    srv_2 = MagicMock()
    srv_2.quit.side_effect = smtplib.SMTPException("Falha quit 2")
    srv_2.close.side_effect = OSError("Falha close 2")

    provider._server = srv_1
    provider._promo_server = srv_2

    provider.close()

    srv_1.quit.assert_called_once()
    srv_1.close.assert_called_once()
    srv_2.quit.assert_called_once()
    srv_2.close.assert_called_once()
    assert provider._server is None
    assert provider._promo_server is None


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_fallback_promo_from_addr_none_assume_promo_user(mock_smtp_ssl, mock_sleep, tmp_path):
    """Quando promo_from_addr=None com promo_user/promo_password válidos, assume promo_user."""
    fabrica_smtp, _ = _criar_fabrica_smtp_por_conta()
    mock_smtp_ssl.side_effect = fabrica_smtp

    config = _criar_config_teste()
    provider = _criar_provider(tmp_path, promo_from_addr=None)
    assert provider.promo_from_addr == EMAIL_COMERCIAL

    service = NotificationService(provider, config)
    assert service.handle_transition(_criar_evento_pedido("99"), "cupom_pedido_3") is True

    envelope_from, _, raw_msg = provider._promo_server.sendmail.call_args[0]
    msg = email_lib.message_from_string(raw_msg)
    assert envelope_from == EMAIL_COMERCIAL
    assert EMAIL_COMERCIAL in msg["From"]
