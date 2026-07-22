import sys
import os
import json
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import load_config
from src.core.client import YampiClient
from src.ports.postgres_repo import PostgresStateRepository
from src.ports.message_provider import DryRunMessageProvider
from src.workers.abandoned_cart import AbandonedCartProcessor
from src.workers.orders import OrderProcessor

# Configuração de logger (escreve no console e no arquivo logs/app.log)
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("debug_main")

class CachedYampiClient:
    """
    Cliente Proxy que intercepta as chamadas para a Yampi.
    Se o JSON de cache (mock) não existir, ele faz um wget (fetch real via API),
    guarda 1000 registros no JSON e depois serve do arquivo.
    Se existir, ele lê o JSON imediatamente, poupando a API e mantendo consistência para o debug.
    """
    def __init__(self, real_client: YampiClient, limit=10):
        self.real_client = real_client
        self.limit = limit
        
        # Garante que a pasta tests existe para salvar os json
        self.cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests"))
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.orders_cache_file = os.path.join(self.cache_dir, "orders_mock.json")
        self.carts_cache_file = os.path.join(self.cache_dir, "carts_mock.json")

    def get_orders(self, filters=None, include=None):
        if os.path.exists(self.orders_cache_file):
            logger.info(f"[CachedYampiClient] Lendo PEDIDOS do arquivo de cache local (limitado a {self.limit}): {self.orders_cache_file}")
            with open(self.orders_cache_file, "r", encoding="utf-8") as f:
                orders = json.load(f)[:self.limit]
            # Retorna um generator para simular o YampiClient original
            return (o for o in orders)
            
        logger.info(f"[CachedYampiClient] Arquivo não encontrado. Buscando {self.limit} PEDIDOS reais na Yampi...")
        orders = []
        generator = self.real_client.get_orders(filters=filters, include=include)
        
        try:
            for idx, order in enumerate(generator):
                if idx >= self.limit:
                    break
                orders.append(order)
                if len(orders) % 100 == 0:
                    logger.info(f"Buscados {len(orders)} pedidos...")
        except Exception as e:
            logger.error(f"Erro ao buscar pedidos na API: {e}")
            
        logger.info(f"[CachedYampiClient] Salvando {len(orders)} pedidos reais no cache {self.orders_cache_file}...")
        with open(self.orders_cache_file, "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
            
        return (o for o in orders)

    def get_abandoned_carts(self, filters=None, include=None):
        if os.path.exists(self.carts_cache_file):
            logger.info(f"[CachedYampiClient] Lendo CARRINHOS do arquivo de cache local (limitado a {self.limit}): {self.carts_cache_file}")
            with open(self.carts_cache_file, "r", encoding="utf-8") as f:
                carts = json.load(f)[:self.limit]
            return (c for c in carts)
            
        logger.info(f"[CachedYampiClient] Arquivo não encontrado. Buscando {self.limit} CARRINHOS reais na Yampi...")
        carts = []
        generator = self.real_client.get_abandoned_carts(filters=filters, include=include)
        
        try:
            for idx, cart in enumerate(generator):
                if idx >= self.limit:
                    break
                carts.append(cart)
                if len(carts) % 100 == 0:
                    logger.info(f"Buscados {len(carts)} carrinhos...")
        except Exception as e:
            logger.error(f"Erro ao buscar carrinhos na API: {e}")
            
        logger.info(f"[CachedYampiClient] Salvando {len(carts)} carrinhos reais no cache {self.carts_cache_file}...")
        with open(self.carts_cache_file, "w", encoding="utf-8") as f:
            json.dump(carts, f, indent=2, ensure_ascii=False)
            
        return (c for c in carts)

if __name__ == "__main__":
    print("=====================================================")
    print("=== MAIN PROVISÓRIA (DEBUG CACHE RUNNER - YAMPI)  ===")
    print("=====================================================")
    
    config = load_config()
    
    # Força MAX_WORKERS = 1 e INTERACTIVE_DEBUG = True para navegação síncrona item a item no VSCode
    config.MAX_WORKERS = 1
    config.INTERACTIVE_DEBUG = True
    
    # Inicializa o Client real da Yampi com as suas credenciais
    real_api_client = YampiClient(
        user_token=config.YAMPI_USER_TOKEN,
        user_secret_key=config.YAMPI_USER_SECRET_KEY,
        merchant_alias=config.YAMPI_ALIAS
    )
    
    # Embrulha o client real no nosso Cache (limite de 10 itens por rodada)
    api_client = CachedYampiClient(real_client=real_api_client, limit=10)
    
    # Provedor de logs apenas (não envia emails reais)
    message_provider = DryRunMessageProvider()
    
    # Banco real de testes (Certifique-se de usar o BD correto de testes localmente)
    state_repo = PostgresStateRepository(config.DATABASE_URL)
    
    input("\n[DEBUG] Pressione ENTER para iniciar o processamento interativo de ORDERS (até 10 itens)...")
    order_processor = OrderProcessor(config, api_client, message_provider, state_repo)
    order_processor.process()
    
    input("\n[DEBUG] Pressione ENTER para iniciar o processamento interativo de CARTS (até 10 itens)...")
    cart_processor = AbandonedCartProcessor(config, api_client, message_provider, state_repo)
    cart_processor.process()
    
    print("\nProcessamento completo!")
