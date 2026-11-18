import logging
import shutil
from pathlib import Path

from src.core.logging_config import SafeRotatingFileHandler, setup_logging


def test_setup_logging_creates_log_and_emails_directories(tmp_path):
    """Garante que setup_logging cria os diretórios de logs e e-mails se não existirem."""
    log_file = tmp_path / "containers" / "logs" / "app.log"
    emails_dir = tmp_path / "containers" / "emails"

    assert not log_file.parent.exists()
    assert not emails_dir.exists()

    setup_logging(verbose=False, log_file=str(log_file), emails_dir=str(emails_dir))

    assert log_file.parent.is_dir()
    assert emails_dir.is_dir()
    assert log_file.exists()


def test_safe_rotating_file_handler_recreates_missing_directory_on_emit(tmp_path):
    """Garante que o handler verifica e recria a pasta de logs antes de escrever se ela for removida."""
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.log"

    handler = SafeRotatingFileHandler(
        str(log_file),
        maxBytes=1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    test_logger = logging.getLogger("test_safe_rotating")
    test_logger.setLevel(logging.INFO)
    test_logger.handlers = [handler]
    test_logger.propagate = False

    test_logger.info("primeira mensagem")
    assert "primeira mensagem" in log_file.read_text(encoding="utf-8")

    # Simula remoção da pasta de logs em tempo de execução
    shutil.rmtree(log_dir)
    assert not log_dir.exists()

    test_logger.info("segunda mensagem apos remocao")

    assert log_dir.is_dir()
    assert log_file.exists()
    assert "segunda mensagem apos remocao" in log_file.read_text(encoding="utf-8")
    handler.close()
