import sys
import os
import logging
from src.core.macros import (
    MACRO_DEFAULT_LOG_PATH,
    MACRO_LOG_MAX_BYTES,
    MACRO_LOG_BACKUP_COUNT
)
from logging.handlers import RotatingFileHandler

_SENTRY_INITIALIZED = False

class SafeRotatingFileHandler(RotatingFileHandler):
    """
    Handler de log rotativo que garante a existência da pasta de destino
    antes de abrir ou gravar cada registro de log.
    """

    def __init__(self, filename: str, *args, **kwargs) -> None:
        log_dir = os.path.dirname(os.path.abspath(filename))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        super().__init__(filename, *args, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        log_dir = os.path.dirname(self.baseFilename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        if self.stream is not None and not os.path.exists(self.baseFilename):
            try:
                self.stream.close()
            finally:
                self.stream = None
        super().emit(record)


def setup_logging(
    verbose: bool = False,
    log_file: str = MACRO_DEFAULT_LOG_PATH,
    emails_dir: str = "local_data/emails",
) -> None:
    """
    Configura o sistema de logging da aplicação.
    Se verbose=True, define o nível de log para DEBUG.
    Caso contrário, mantém o nível padrão em INFO.
    """
    global _SENTRY_INITIALIZED
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else "local_data/logs", exist_ok=True)
    if emails_dir:
        os.makedirs(emails_dir, exist_ok=True)
    
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn and not _SENTRY_INITIALIZED:
        try:
            import sentry_sdk
            traces_rate = float(os.environ.get("TRACES_SAMPLE_RATE", "1.0"))
            env_name = os.environ.get("ENVIRONMENT", "production")
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=traces_rate,
                environment=env_name,
                send_default_pii=False, # Data Scrubbing habilitado (ignora dados sensíveis e PII locais)
            )
            _SENTRY_INITIALIZED = True
        except (ImportError, Exception) as e:
            logging.warning(f"Não foi possível inicializar o Sentry SDK: {e}")
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    from src.core.time_utils import get_now_utc

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    formatter.converter = lambda *args: get_now_utc().timetuple()

    # Reconfigura handlers do logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove handlers antigos para evitar duplicidade em recargas
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)
    root_logger.addHandler(stream_handler)
    
    file_handler = SafeRotatingFileHandler(
        log_file,
        maxBytes=MACRO_LOG_MAX_BYTES,
        backupCount=MACRO_LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    _setup_global_exception_hooks(root_logger)
    
    logging.info(f"Sistema de logging inicializado. Nível: {'DEBUG (Verbose)' if verbose else 'INFO'}")

def _setup_global_exception_hooks(logger: logging.Logger) -> None:
    """
    Configura os interceptadores globais para garantir que nenhuma exceção vaze sem log.
    """
    import threading

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Deixa o Ctrl+C funcionar normalmente
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        logger.critical(
            "=================== FATAL ERROR ===================\n"
            "Exceção Não Tratada Global capturada pelo sys.excepthook!\n"
            f"Tipo: {exc_type.__name__} | Valor: {exc_value}\n"
            "A stack trace foi enviada ao Sentry (se configurado).\n"
            "A aplicação será encerrada logo após este log."
        )
        
        try:
            import sentry_sdk
            sentry_sdk.capture_exception((exc_type, exc_value, exc_traceback))
        except Exception:
            pass

    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
            
        logger.critical(
            "=================== THREAD FATAL ERROR ===================\n"
            f"Exceção Não Tratada na Thread '{args.thread.name}' capturada pelo threading.excepthook!\n"
            f"Tipo: {args.exc_type.__name__} | Valor: {args.exc_value}\n"
            "A stack trace foi enviada ao Sentry (se configurado).\n"
            "A thread morreu silenciosamente."
        )
        
        try:
            import sentry_sdk
            sentry_sdk.capture_exception((args.exc_type, args.exc_value, args.exc_traceback))
        except Exception:
            pass

    sys.excepthook = handle_unhandled_exception
    
    if hasattr(threading, 'excepthook'):
        threading.excepthook = handle_thread_exception

