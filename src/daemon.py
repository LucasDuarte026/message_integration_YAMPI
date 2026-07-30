import time
import logging
import os
import sys

# Garante que as importações relativas funcionem a partir da raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ao importar run_all, as configurações globais de logging em main.py serão ativadas
from src.main import run_all
from src.core.logging_config import setup_logging

# Lê a flag VERBOSE do ambiente para permitir controle dinâmico no docker-compose
is_verbose = os.environ.get("VERBOSE", "0").lower() in ("1", "true", "yes")

# Força a configuração de logs para que o FileHandler grave no app.log corretamente
setup_logging(verbose=is_verbose, log_file="local_data/logs/app.log")

logger = logging.getLogger("daemon")

def main():
    INTERVALO_SEGUNDOS = 300 # 5 minutos
    
    logger.info("=====================================================")
    logger.info("=== INICIANDO DAEMON DO MESSAGE INTEGRATION ===")
    logger.info(f"=== Intervalo: {INTERVALO_SEGUNDOS} segundos===")
    logger.info("=== O modo de disparo é definido em src/core/macros.py ===")
    logger.info("=====================================================")
    
    while True:
        try:
            logger.info("--- [DAEMON] Iniciando novo ciclo de processamento ---")
            run_all()
            logger.info("--- [DAEMON] Ciclo concluído com sucesso ---")
        except Exception as e:
            logger.error(f"[DAEMON] Erro não tratado durante o ciclo: {e}", exc_info=True)
            
        logger.info(f"[DAEMON] Dormindo por {INTERVALO_SEGUNDOS} segundos...")
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
    main()
