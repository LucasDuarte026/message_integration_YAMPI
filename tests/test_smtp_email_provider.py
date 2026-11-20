import smtplib
from unittest.mock import MagicMock, patch
import pytest

from src.ports.smtp_email_provider import SMTPEmailProvider


def test_mask_email():
    """Verifica o mascaramento LGPD de e-mails para logs."""
    provider = SMTPEmailProvider("smtp.host.com", 587, "user", "pass", "from@host.com")

    assert provider._mask_email("claucimardi11@gmail.com") == "clauc*******1@gmail.com"
    assert provider._mask_email("ana@teste.com") == "a*a@teste.com"
    assert provider._mask_email("ab@teste.com") == "**@teste.com"
    assert provider._mask_email("") == "***@***"
    assert provider._mask_email("sem_arroba") == "***@***"


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_send_email_message_success_with_cid_and_ssl(mock_smtp_ssl, mock_sleep, tmp_path):
    """Testa envio via SMTP SSL (porta 465), anexo inline CID modular e throttling."""
    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.return_value = mock_server

    img_dir = tmp_path / "social_icons"
    img_dir.mkdir(parents=True)
    fake_webp = img_dir / "whatsapp_q50.webp"
    fake_webp.write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")

    provider = SMTPEmailProvider(
        "smtp.host.com",
        465,
        "user@host.com",
        "secret",
        None,
        assets_dir=str(tmp_path),
    )
    html_body = (
        '<html><body>'
        '<img src="src/templates/emails/assets/images/social_icons/whatsapp_q50.webp" />'
        '<img src="nao_existe/arquivo.png" />'
        '</body></html>'
    )

    result = provider.send_email_message("cliente@exemplo.com", "Assunto Teste", html_body)

    assert result is True
    mock_smtp_ssl.assert_called_once()
    mock_server.login.assert_called_once_with("user@host.com", "secret")
    mock_server.sendmail.assert_called_once()

    raw_msg = mock_server.sendmail.call_args[0][2]
    assert "Content-ID: <img_" in raw_msg
    assert "Content-Disposition: inline" in raw_msg

    import email as email_lib
    parsed_msg = email_lib.message_from_string(raw_msg)
    html_parts = [
        part.get_payload(decode=True).decode("utf-8")
        for part in parsed_msg.walk()
        if part.get_content_type() == "text/html"
    ]
    assert html_parts and "cid:img_" in html_parts[0]
    mock_sleep.assert_called_once()


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP")
def test_send_email_message_retries_on_disconnect_and_fails_after_max_retries(mock_smtp, mock_sleep):
    """Testa envio STARTTLS (porta 587), retry após desconexão e falha após esgotar tentativas."""
    mock_server = MagicMock()
    mock_server.sendmail.side_effect = [
        smtplib.SMTPServerDisconnected("Caiu"),
        smtplib.SMTPException("Erro SMTP"),
        OSError("Socket fechado"),
    ]
    mock_smtp.return_value = mock_server

    provider = SMTPEmailProvider("smtp.host.com", 587, "user@host.com", "secret", "from@host.com")
    result = provider.send_email_message("cliente@exemplo.com", "Assunto", "<p>Olá</p>")

    assert result is False
    assert mock_server.starttls.call_count == 3
    assert mock_server.sendmail.call_count == 3
    assert mock_sleep.call_count == 2


def test_smtp_close():
    """Verifica que close() encerra conexão SMTP ativa com segurança e trata exceção em quit()."""
    provider = SMTPEmailProvider("smtp.host.com", 587, "user", "pass", "from@host.com")

    # Cenário 1: quit() funciona normalmente
    mock_server = MagicMock()
    provider._server = mock_server
    provider.close()
    mock_server.quit.assert_called_once()
    assert provider._server is None

    # Cenário 2: quit() falha e faz fallback para close()
    mock_server_err = MagicMock()
    mock_server_err.quit.side_effect = smtplib.SMTPException("Falha no quit")
    provider._server = mock_server_err
    provider.close()
    mock_server_err.close.assert_called_once()
    assert provider._server is None


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_send_email_message_rfc5322_headers_and_mime_order(mock_smtp_ssl, mock_sleep, tmp_path):
    """Valida EmailMessage, cabeçalhos RFC 5322, ordem text/plain -> text/html e WebP inline."""
    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.return_value = mock_server

    img_dir = tmp_path / "social_icons"
    img_dir.mkdir(parents=True)
    (img_dir / "whatsapp_q50.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")

    provider = SMTPEmailProvider(
        "smtp.host.com",
        465,
        "contato@elevemeloja.com.br",
        "secret",
        "contato@elevemeloja.com.br",
        assets_dir=str(tmp_path),
    )
    html_body = (
        '<html><body><p>Pedido aprovado!</p>'
        '<img src="src/templates/emails/assets/images/social_icons/whatsapp_q50.webp" />'
        '</body></html>'
    )
    result = provider.send_email_message(
        "cliente@exemplo.com",
        "Eleveme: Pagamento confirmado",
        html_body,
        plain_text="Pedido aprovado! Obrigado por comprar na Eleveme.",
        is_promotional=False,
    )

    assert result is True
    raw_msg = mock_server.sendmail.call_args[0][2]

    import email as email_lib
    parsed = email_lib.message_from_string(raw_msg)

    assert parsed["Message-ID"] is not None
    assert "@elevemeloja.com.br>" in parsed["Message-ID"]
    assert parsed["Date"] is not None
    assert "Eleveme" in parsed["From"]
    assert "contato@elevemeloja.com.br" in parsed["From"]
    assert parsed["Reply-To"] is not None
    assert "comercial@elevemeloja.com.br" in parsed["Reply-To"]
    # Transacional puro não deve injetar List-Unsubscribe
    assert parsed["List-Unsubscribe"] is None
    assert parsed["List-Unsubscribe-Post"] is None

    content_types = [part.get_content_type() for part in parsed.walk()]
    assert "text/plain" in content_types
    assert "text/html" in content_types
    assert content_types.index("text/plain") < content_types.index("text/html")
    assert "image/webp" in content_types


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_send_email_message_promotional_injects_rfc8058_and_skips_https_cid(mock_smtp_ssl, mock_sleep):
    """Valida List-Unsubscribe One-Click (RFC 8058) em e-mail promocional e zero CID para HTTPS."""
    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.return_value = mock_server

    provider = SMTPEmailProvider("smtp.host.com", 465, "contato@elevemeloja.com.br", "secret", None)
    html_body = '<html><body><img src="https://elevemeloja.com.br/banner_q50.webp" /><p>Oferta</p></body></html>'

    result = provider.send_email_message(
        "cliente@exemplo.com",
        "Eleveme: Lembrete sobre seu carrinho",
        html_body,
        plain_text="Lembrete sobre seu carrinho",
        is_promotional=True,
    )

    assert result is True
    raw_msg = mock_server.sendmail.call_args[0][2]

    import email as email_lib
    parsed = email_lib.message_from_string(raw_msg)

    assert parsed["List-Unsubscribe"] is not None
    assert "https://elevemeloja.com.br/unsubscribe" in parsed["List-Unsubscribe"]
    assert parsed["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    content_types = [part.get_content_type() for part in parsed.walk()]
    assert not any(ct.startswith("image/") for ct in content_types)


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_send_email_message_resolves_custom_assets_dir_and_graceful_when_missing(mock_smtp_ssl, mock_sleep, tmp_path):
    """Valida mapeamento modular de assets_dir e degradação graciosa quando a pasta não existe (modo open source)."""
    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.return_value = mock_server

    # 1. Pasta externa existente fora do repositório
    external_dir = tmp_path / "external_email_assets"
    banner_dir = external_dir / "email_1_pedido_aprovado" / "body"
    banner_dir.mkdir(parents=True)
    (banner_dir / "pedido_aprovado_q50.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")

    provider = SMTPEmailProvider(
        "smtp.host.com",
        465,
        "contato@elevemeloja.com.br",
        "secret",
        None,
        assets_dir=str(external_dir),
    )
    html_body = '<html><body><img src="src/templates/emails/assets/images/email_1_pedido_aprovado/body/pedido_aprovado_q50.webp" /></body></html>'
    assert provider.send_email_message("cliente@exemplo.com", "Pedido", html_body, plain_text="Pedido") is True

    import email as email_lib
    parsed = email_lib.message_from_string(mock_server.sendmail.call_args[0][2])
    assert "image/webp" in [part.get_content_type() for part in parsed.walk()]

    # 2. Pasta ausente (clone open source sem imagens privadas) não deve quebrar o envio
    missing_provider = SMTPEmailProvider(
        "smtp.host.com",
        465,
        "contato@elevemeloja.com.br",
        "secret",
        None,
        assets_dir=str(tmp_path / "pasta_inexistente"),
    )
    assert missing_provider.send_email_message("cliente@exemplo.com", "Pedido", html_body, plain_text="Pedido") is True


@patch("src.ports.smtp_email_provider.time.sleep", return_value=None)
@patch("src.ports.smtp_email_provider.smtplib.SMTP_SSL")
def test_send_email_message_routes_promotional_vs_transactional_senders(mock_smtp_ssl, mock_sleep):
    """Valida roteamento de remetente/autenticação: oficial@ para avisos e comercial@ para promoções."""
    trans_server = MagicMock()
    trans_server.noop.return_value = (250, b"OK")
    promo_server = MagicMock()
    promo_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.side_effect = [trans_server, promo_server]

    provider = SMTPEmailProvider(
        "smtp.hostinger.com",
        465,
        "oficial@elevemeloja.com.br",
        "senha_oficial",
        "oficial@elevemeloja.com.br",
        promo_user="comercial@elevemeloja.com.br",
        promo_password="senha_comercial",
        promo_from_addr="comercial@elevemeloja.com.br",
    )

    # 1. Aviso transacional (is_promotional=False) -> oficial@
    assert provider.send_email_message("cli@exemplo.com", "Pedido aprovado", "<p>Ok</p>", plain_text="Ok", is_promotional=False) is True
    trans_server.login.assert_called_once_with("oficial@elevemeloja.com.br", "senha_oficial")
    assert trans_server.sendmail.call_args[0][0] == "oficial@elevemeloja.com.br"
    assert "oficial@elevemeloja.com.br" in trans_server.sendmail.call_args[0][2]

    # 2. Promocional / Cupom (is_promotional=True) -> comercial@
    assert provider.send_email_message("cli@exemplo.com", "Cupom", "<p>10%</p>", plain_text="10%", is_promotional=True) is True
    promo_server.login.assert_called_once_with("comercial@elevemeloja.com.br", "senha_comercial")
    assert promo_server.sendmail.call_args[0][0] == "comercial@elevemeloja.com.br"
    assert "comercial@elevemeloja.com.br" in promo_server.sendmail.call_args[0][2]

    # 3. close() encerra ambos os pools SMTP
    provider.close()
    trans_server.quit.assert_called_once()
    promo_server.quit.assert_called_once()
