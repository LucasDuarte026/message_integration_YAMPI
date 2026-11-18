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
def test_send_email_message_success_with_cid_and_ssl(mock_smtp_ssl, mock_sleep):
    """Testa envio via SMTP SSL (porta 465), anexo inline CID e throttling."""
    mock_server = MagicMock()
    mock_server.noop.return_value = (250, b"OK")
    mock_smtp_ssl.return_value = mock_server

    provider = SMTPEmailProvider("smtp.host.com", 465, "user@host.com", "secret", None)
    html_body = (
        '<html><body>'
        '<img src="src/templates/emails/assets/images/social_icons/whatsapp.png" />'
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
