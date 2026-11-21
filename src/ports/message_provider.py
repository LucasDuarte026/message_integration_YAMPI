import os
import logging
from typing import Optional
from src.domain.interfaces import MessageProviderProtocol

logger = logging.getLogger(__name__)

class DryRunMessageProvider(MessageProviderProtocol):
    """
    Mock Provider para testes (Dry-Run).
    Em vez de chamar uma API real e gastar créditos, ele apenas loga no terminal.
    Cumpre estritamente o contrato da interface.
    """
        
    def send_email_message(
        self,
        email: str,
        subject: str,
        html_body: str,
        plain_text: Optional[str] = None,
        is_promotional: bool = False,
        email_type: Optional[str] = None,
    ) -> bool:
        logger.info("="*40)
        logger.info(f"[DRY-RUN] Enviando Email para: {email}")
        if email_type:
            logger.info(f"[DRY-RUN] Tipo de E-mail: {email_type}")
        logger.info(f"[DRY-RUN] Assunto: {subject}")
        logger.info("="*40)
        
        logger.info(f"[DRY-RUN] E-mail processado e registrado com sucesso para {email}!")

            
        return True

