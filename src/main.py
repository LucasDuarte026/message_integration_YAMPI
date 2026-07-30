import logging
import sys
import os
import argparse
from typing import Optional

# Adiciona o diretório raiz do projeto ao sys.path para garantir importações relativas a partir de 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import load_config
from src.core.client import YampiClient
from src.ports.postgres_repo import PostgresStateRepository
from src.ports.message_provider import DryRunMessageProvider
from src.ports.smtp_email_provider import SMTPEmailProvider
from src.workers.abandoned_cart import AbandonedCartProcessor
from src.workers.orders import OrderProcessor
from src.core import macros

# Garante que a pasta de logs exista
os.makedirs("local_data/logs", exist_ok=True)

# Configuração global de log para o ponto de entrada principal (escreve no console e no arquivo)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("local_data/logs/app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def get_dependencies():
    logger.info("Carregando configurações...")
    config = load_config()
    
    logger.info(f"=== Message Integration (v{config.APP_VERSION}) ===")
    logger.info("Inicializando dependências do sistema (Spec-Driven)...")
    
    api_client = YampiClient(
        user_token=config.YAMPI_USER_TOKEN,
        user_secret_key=config.YAMPI_USER_SECRET_KEY,
        merchant_alias=config.YAMPI_ALIAS
    )
    
    state_repo = PostgresStateRepository(config.DATABASE_URL)
    
    if not macros.MACRO_ENABLE_REAL_EMAIL_DISPATCH:
        logger.info("Executando em DRY-RUN MODE (Mocks ativos conforme macros.py)")
        message_provider = DryRunMessageProvider()
    else:
        logger.info("Executando em MODO PRODUÇÃO (Disparo real via SMTP conforme macros.py)")
        if not config.SMTP_USER or not config.SMTP_PASSWORD:
            logger.error("Erro: SMTP_USER e SMTP_PASSWORD devem ser configurados para rodar em produção.")
            sys.exit(1)
        message_provider = SMTPEmailProvider(
            host=config.SMTP_HOST,
            port=config.SMTP_PORT,
            user=config.SMTP_USER,
            password=config.SMTP_PASSWORD,
            from_addr=config.SMTP_FROM
        )
        
    return config, api_client, state_repo, message_provider

def run_abandoned_carts():
    config, api_client, state_repo, message_provider = get_dependencies()
    processor = AbandonedCartProcessor(config, api_client, message_provider, state_repo)
    processor.process()

def run_orders():
    config, api_client, state_repo, message_provider = get_dependencies()
    processor = OrderProcessor(config, api_client, message_provider, state_repo)
    processor.process()

def run_all():
    config, api_client, state_repo, message_provider = get_dependencies()
    logger.info("--- Executando Worker de Pedidos ---")
    order_processor = OrderProcessor(config, api_client, message_provider, state_repo)
    order_processor.process()
    
    logger.info("--- Executando Worker de Carrinhos Abandonados ---")
    cart_processor = AbandonedCartProcessor(config, api_client, message_provider, state_repo)
    cart_processor.process()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Message Integration - Workers Orquestrator")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    cart_parser = subparsers.add_parser("abandoned-carts", help="Processar carrinhos abandonados.")
    orders_parser = subparsers.add_parser("orders", help="Processar pedidos recentes (pagamentos e envios).")
    all_parser = subparsers.add_parser("all", help="Processar ambos (pedidos e carrinhos).")
    
    args = parser.parse_args()
    
    if args.command == "abandoned-carts":
        run_abandoned_carts()
    elif args.command == "orders":
        run_orders()
    elif args.command == "all":
        run_all()
    else:
        parser.print_help()
