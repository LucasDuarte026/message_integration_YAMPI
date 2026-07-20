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
from src.ports.whatsapp_meta_provider import WhatsAppMetaProvider
from src.ports.smtp_email_provider import SMTPEmailProvider
from src.workers.abandoned_cart import AbandonedCartProcessor
from src.workers.orders import OrderProcessor

# Garante que a pasta de logs exista
os.makedirs("logs", exist_ok=True)

# Configuração global de log para o ponto de entrada principal (escreve no console e no arquivo)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

def get_dependencies(mock_mode: bool = True):
    logger.info("Carregando configurações...")
    config = load_config()
    
    logger.info("Inicializando dependências do sistema (Spec-Driven)...")
    
    api_client = YampiClient(
        user_token=config.YAMPI_USER_TOKEN,
        user_secret_key=config.YAMPI_USER_SECRET_KEY,
        merchant_alias=config.YAMPI_ALIAS
    )
    
    state_repo = PostgresStateRepository(config.DATABASE_URL)
    
    if mock_mode:
        logger.info("Executando em DRY-RUN MODE (Mocks ativos)")
        message_provider = DryRunMessageProvider()
    else:
        logger.info("Executando em MODO PRODUÇÃO (Disparo real via SMTP)")
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

def run_abandoned_carts(mock_mode: bool = True):
    config, api_client, state_repo, message_provider = get_dependencies(mock_mode)
    processor = AbandonedCartProcessor(config, api_client, message_provider, state_repo)
    processor.process()

def run_orders(mock_mode: bool = True):
    config, api_client, state_repo, message_provider = get_dependencies(mock_mode)
    processor = OrderProcessor(config, api_client, message_provider, state_repo)
    processor.process()

def run_all(mock_mode: bool = True):
    config, api_client, state_repo, message_provider = get_dependencies(mock_mode)
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
    cart_parser.add_argument("--production", action="store_true", help="Desativar o modo Dry-Run (Mock)")
    
    orders_parser = subparsers.add_parser("orders", help="Processar pedidos recentes (pagamentos e envios).")
    orders_parser.add_argument("--production", action="store_true", help="Desativar o modo Dry-Run (Mock)")
    
    all_parser = subparsers.add_parser("all", help="Processar ambos (pedidos e carrinhos).")
    all_parser.add_argument("--production", action="store_true", help="Desativar o modo Dry-Run (Mock)")
    
    args = parser.parse_args()
    
    if args.command == "abandoned-carts":
        run_abandoned_carts(mock_mode=not args.production)
    elif args.command == "orders":
        run_orders(mock_mode=not args.production)
    elif args.command == "all":
        run_all(mock_mode=not args.production)
    else:
        parser.print_help()
