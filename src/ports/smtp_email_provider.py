import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from src.domain.interfaces import MessageProviderProtocol

logger = logging.getLogger(__name__)

class SMTPEmailProvider(MessageProviderProtocol):
    """
    Adaptador concreto para envio de E-mail utilizando o protocolo SMTP.
    Suporta conexão segura via SSL ou TLS (portas 465/587).
    """
    def __init__(self, host: str, port: int, user: Optional[str], password: Optional[str], from_addr: Optional[str]):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_addr = from_addr or user or "recuperacao@sualoja.com"

    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        logger.warning("SMTPEmailProvider não suporta envio de WhatsApp.")
        return False

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = email
            
            # Garante cabeçalho com UTF-8 para evitar problemas de caracteres especiais
            msg.set_charset("utf-8")
            
            part = MIMEText(html_body, "html", "utf-8")
            msg.attach(part)
            
            # Conexão SSL direta na porta 465 ou TLS com STARTTLS na porta 587/outras
            if self.port == 465:
                logger.info(f"Estabelecendo conexão SMTP segura (SSL) com {self.host}:{self.port}...")
                server = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                logger.info(f"Estabelecendo conexão SMTP (STARTTLS) com {self.host}:{self.port}...")
                server = smtplib.SMTP(self.host, self.port, timeout=15)
                server.starttls()
            
            # Login se credenciais fornecidas
            if self.user and self.password:
                logger.info(f"Autenticando usuário SMTP '{self.user}'...")
                server.login(self.user, self.password)
            
            logger.info(f"Despachando mensagem SMTP para {email}...")
            server.sendmail(self.from_addr, [email], msg.as_string())
            server.quit()
            
            logger.info(f"E-mail enviado com sucesso via SMTP para: {email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP para {email}: {e}")
            return False
