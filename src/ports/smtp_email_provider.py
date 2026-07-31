import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Optional
import re
import os
import mimetypes
import uuid
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

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
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
            
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
            
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
            server.sendmail(self.from_addr, [email], msg_root.as_string())
            server.quit()
            
            logger.info(f"E-mail enviado com sucesso via SMTP para: {email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP para {email}: {e}")
            return False
