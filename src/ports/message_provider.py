import logging
from src.domain.interfaces import MessageProviderProtocol

logger = logging.getLogger(__name__)

class DryRunMessageProvider(MessageProviderProtocol):
    """
    Mock Provider para testes (Dry-Run).
    Em vez de chamar uma API real e gastar créditos, ele apenas loga no terminal.
    Cumpre estritamente o contrato da interface.
    """
    
    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        logger.info("="*40)
        logger.info(f"[DRY-RUN] Enviando WhatsApp para: {phone_number}")
        logger.info(f"[DRY-RUN] Conteúdo da Mensagem:\n{message}")
        logger.info("="*40)
        return True
        
    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        logger.info("="*40)
        logger.info(f"[DRY-RUN] Enviando Email para: {email}")
        logger.info(f"[DRY-RUN] Assunto: {subject}")
        logger.info(f"[DRY-RUN] Corpo HTML:\n{html_body}")
        logger.info("="*40)
        return True
