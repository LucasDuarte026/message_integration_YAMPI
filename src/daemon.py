import time
import logging
import os
import sys

# Garante que as importações relativas funcionem a partir da raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ao importar run_all, as configurações globais de logging em main.py serão ativadas
from src.main import run_all
from src.core.logging_config import setup_logging
from src.core.macros import MACRO_DAEMON_SLEEP_INTERVAL_SEG

try:
    import sentry_sdk
    import sentry_sdk.crons
except ImportError:
    sentry_sdk = None

# Lê a flag VERBOSE do ambiente para permitir controle dinâmico no docker-compose
is_verbose = os.environ.get("VERBOSE", "0").lower() in ("1", "true", "yes")

# Força a configuração de logs para que o FileHandler grave no app.log corretamente
setup_logging(verbose=is_verbose, log_file="local_data/logs/app.log")

logger = logging.getLogger("daemon")

def main():
    logger.info("=====================================================")
    logger.info("=== INICIANDO DAEMON DO MESSAGE INTEGRATION ===")
    logger.info(f"=== Intervalo: {MACRO_DAEMON_SLEEP_INTERVAL_SEG} segundos===")
    logger.info("=== O modo de disparo é definido em src/core/macros.py ===")
    logger.info("=====================================================")
    
    while True:
        try:
            logger.info("--- [DAEMON] Iniciando novo ciclo de processamento ---")
            if sentry_sdk and hasattr(sentry_sdk, "crons"):
                with sentry_sdk.crons.monitor(monitor_slug="yampi-daemon-cycle"):
                    run_all()
            else:
                run_all()
            logger.info("--- [DAEMON] Ciclo concluído com sucesso ---")
        except Exception as e:
            logger.error(f"[DAEMON] Erro não tratado durante o ciclo: {e}", exc_info=True)
            
        logger.info(f"[DAEMON] Dormindo por {MACRO_DAEMON_SLEEP_INTERVAL_SEG} segundos...")
        time.sleep(MACRO_DAEMON_SLEEP_INTERVAL_SEG)

if __name__ == "__main__":
    main()
