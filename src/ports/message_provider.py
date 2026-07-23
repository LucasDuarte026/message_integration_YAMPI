import os
import logging
from src.domain.interfaces import MessageProviderProtocol

logger = logging.getLogger(__name__)

class DryRunMessageProvider(MessageProviderProtocol):
    """
    Mock Provider para testes (Dry-Run).
    Em vez de chamar uma API real e gastar créditos, ele apenas loga no terminal.
    Cumpre estritamente o contrato da interface.
    """
        
    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        logger.info("="*40)
        logger.info(f"[DRY-RUN] Enviando Email para: {email}")
        logger.info(f"[DRY-RUN] Assunto: {subject}")
        logger.info("="*40)
        
        # Salva o arquivo HTML localmente em tests/ para inspeção visual do desenvolvedor
        target_dir = "tests"
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, "temp_email_output.html")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_body)
            logger.info(f"[DRY-RUN] E-mail de teste salvo com sucesso!")
            logger.info(f"[DRY-RUN] Acesse: file://{os.path.abspath(file_path)} no seu navegador!")
        except Exception as e:
            logger.error(f"[DRY-RUN] Erro ao salvar o HTML do e-mail localmente: {e}")
            
        return True

