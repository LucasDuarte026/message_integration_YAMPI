import requests
import logging
from src.domain.interfaces import MessageProviderProtocol

logger = logging.getLogger(__name__)

class WhatsAppMetaProvider(MessageProviderProtocol):
    """
    Adaptador concreto para envio de WhatsApp utilizando a Cloud API oficial da Meta.
    """
    def __init__(self, token: str, phone_number_id: str, template_name: str = "hello_world", language_code: str = "en_US"):
        self.token = token
        self.phone_number_id = phone_number_id
        self.template_name = template_name
        self.language_code = language_code
        self.base_url = f"https://graph.facebook.com/v20.0/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        # A Meta exige formato internacional puro sem o caractere '+' ou caracteres especiais
        clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
        
        # Estrutura base de template exigida pela Meta
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": self.template_name,
                "language": {
                    "code": self.language_code
                }
            }
        }
        
        # Se for um template customizado (diferente de hello_world), injeta a mensagem como variável do template.
        if self.template_name != "hello_world" and message:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            ]
            
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensagem de template WhatsApp enviada com sucesso para {phone_number}.")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem via WhatsApp Meta Cloud API: {e}")
            return False

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        # A API do WhatsApp não envia e-mails, então este provedor retorna falso para e-mails.
        logger.warning("WhatsAppMetaProvider não suporta o envio de e-mails.")
        return False
