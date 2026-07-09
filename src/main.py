import logging
import sys
import os
import argparse
from typing import Optional

# Adiciona o diretório raiz do projeto ao sys.path para garantir importações relativas a partir de 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import load_config
from src.core.client import YampiClient
from src.core.db import SQLiteStateRepository
from src.ports.message_provider import DryRunMessageProvider
from src.workers.abandoned_cart import AbandonedCartProcessor

# Configuração global de log para o ponto de entrada principal
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_abandoned_carts(mock_mode: bool = True):
    """
    Instancia as dependências e executa o processador de carrinhos abandonados.
    """
    logger.info("Carregando configurações...")
    config = load_config()
    
    logger.info("Inicializando dependências do sistema (Spec-Driven)...")
    
    # 1. Yampi Client (Infa/Provider)
    api_client = YampiClient(
        user_token=config.YAMPI_USER_TOKEN,
        user_secret_key=config.YAMPI_USER_SECRET_KEY,
        merchant_alias=config.YAMPI_ALIAS
    )
    
    # 2. State Repository (Persistência)
    state_repo = SQLiteStateRepository(config)
    
    # 3. Message Provider (Mensageria)
    if mock_mode:
        logger.info("Executando em DRY-RUN MODE (Mocks ativos)")
        message_provider = DryRunMessageProvider()
    else:
        # Futuramente: TwilioMessageProvider() ou ZenviaMessageProvider()
        logger.error("Modo produção de mensageria ainda não implementado (Future Implementations).")
        sys.exit(1)
        
    # Orquestração do Worker
    processor = AbandonedCartProcessor(
        config=config,
        api_client=api_client,
        message_provider=message_provider,
        state_repo=state_repo
    )
    
    # Execução
    processor.process()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Message Integration - Workers Orquestrator")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando para carrinhos abandonados
    cart_parser = subparsers.add_parser("abandoned-carts", help="Processar carrinhos abandonados.")
    cart_parser.add_argument("--production", action="store_true", help="Desativar o modo Dry-Run (Mock)")
    
    args = parser.parse_args()
    
    if args.command == "abandoned-carts":
        run_abandoned_carts(mock_mode=not args.production)
    else:
        parser.print_help()
