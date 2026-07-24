import os
import sys
import logging

def setup_logging(verbose: bool = False, log_file: str = "logs/app.log") -> None:
    """
    Configura o sistema de logging da aplicação.
    Se verbose=True, define o nível de log para DEBUG.
    Caso contrário, mantém o nível padrão em INFO.
    """
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else "logs", exist_ok=True)
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

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
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Sistema de logging inicializado. Nível: {'DEBUG (Verbose)' if verbose else 'INFO'}")
