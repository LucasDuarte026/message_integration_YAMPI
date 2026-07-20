import os
import time
import logging
from typing import Dict, Any, Generator, Optional, List
import requests

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class YampiClient:
    """
    Cliente Python para conectar e buscar dados na API V2 da Yampi.
    
    Documentação de referência:
    - Introdução: https://docs.yampi.com.br/api-reference/introduction
    - Autenticação: https://docs.yampi.com.br/api-reference/auth/auth-user-token
    """
    
    BASE_URL = "https://api.dooki.com.br/v2"

    def __init__(self, user_token: str, user_secret_key: str, merchant_alias: Optional[str] = None):
        """
        Inicializa o cliente com as credenciais da API.
        
        :param user_token: Token do usuário obtido no painel da Yampi.
        :param user_secret_key: Chave secreta do usuário obtida no painel da Yampi.
        :param merchant_alias: Alias da loja (opcional). Se não informado, o cliente tentará 
                               descobri-lo automaticamente chamando o endpoint de autenticação.
        """
        self.user_token = user_token
        self.user_secret_key = user_secret_key
        self.headers = {
            "Content-Type": "application/json",
            "User-Token": self.user_token,
            "User-Secret-Key": self.user_secret_key
        }
        self._merchant_alias = merchant_alias

    @property
    def merchant_alias(self) -> str:
        """
        Retorna o alias do merchant. Caso não tenha sido informado, resolve-o via API.
        """
        if not self._merchant_alias:
            logger.info("Merchant Alias não fornecido. Tentando descobrir automaticamente...")
            self._merchant_alias = self._fetch_merchant_alias()
        return self._merchant_alias

    def _fetch_merchant_alias(self) -> str:
        """
        Chama o endpoint POST /auth/me para obter as lojas (merchants) associadas
        ao token e retorna o alias da primeira loja ativa encontrada.
        """
        url = f"{self.BASE_URL}/auth/me"
        try:
            # POST /auth/me não exige body
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            merchants = data.get("data", {}).get("merchants", {}).get("data", [])
            if not merchants:
                raise ValueError("Nenhuma loja (merchant) foi encontrada para estas credenciais.")
            
            # Procura a primeira loja ativa
            for merchant in merchants:
                if merchant.get("active"):
                    alias = merchant.get("alias")
                    logger.info(f"Loja ativa encontrada: '{merchant.get('name')}' (alias: {alias})")
                    return alias
            
            # Fallback para a primeira loja independente do status
            alias = merchants[0].get("alias")
            logger.info(f"Nenhuma loja ativa encontrada. Usando a primeira loja: '{merchants[0].get('name')}' (alias: {alias})")
            return alias
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro ao verificar credenciais: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar dados do usuário: {str(e)}")
            raise

    def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, 
                json_data: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Dict[str, Any]:
        """
        Faz uma requisição HTTP para a API da Yampi tratando paginação, cache e Rate Limits (HTTP 429).
        
        :param method: Método HTTP (GET, POST, PUT, DELETE).
        :param path: Caminho do endpoint (sem a URL base e sem o alias, ex: 'orders' ou 'catalog/products').
        :param params: Parâmetros de consulta (Query Params).
        :param json_data: Corpo da requisição no formato JSON.
        :param max_retries: Número máximo de tentativas em caso de erro 429 (Rate Limit).
        :return: Dicionário correspondente à resposta JSON da API.
        """
        # Garante o alias no início do path se for um endpoint específico de loja
        # Endpoints globais como 'auth/me' ou 'auth' não levam o alias
        if path.startswith("auth/") or path == "auth":
            url = f"{self.BASE_URL}/{path}"
        else:
            url = f"{self.BASE_URL}/{self.merchant_alias}/{path}"

        # Parâmetros padrão: por padrão ignoramos o cache em GET para garantir dados frescos
        # O cache padrão na Yampi é de 30 minutos
        query_params = params or {}
        if method.upper() == "GET" and "skipCache" not in query_params:
            query_params["skipCache"] = "true"

        retry_count = 0
        backoff_delay = 2.0  # tempo inicial de espera para Rate Limit em segundos

        while retry_count <= max_retries:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=query_params,
                    json=json_data
                )
                
                # Trata Rate Limit (HTTP 429)
                if response.status_code == 429:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error("Limite máximo de tentativas atingido após receber HTTP 429.")
                        response.raise_for_status()
                    
                    # Loga os headers de Rate Limit se presentes
                    limit = response.headers.get("X-RateLimit-Limit")
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    logger.warning(
                        f"Rate limit atingido (HTTP 429). Limite: {limit}, Restantes: {remaining}. "
                        f"Aguardando {backoff_delay} segundos antes da tentativa {retry_count}/{max_retries}..."
                    )
                    time.sleep(backoff_delay)
                    backoff_delay *= 2  # Aumento exponencial do delay
                    continue
                
                # Levanta exceção para outros códigos de erro (4xx e 5xx)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na requisição ({method} {url}): {str(e)}")
                raise

        raise requests.exceptions.RetryError("Falha na requisição devido ao excesso de retentativas de Rate Limit.")

    def get_paginated_data(self, path: str, params: Optional[Dict[str, Any]] = None, 
                           limit_per_page: int = 100) -> Generator[Dict[str, Any], None, None]:
        """
        Gera itens iterando automaticamente por todas as páginas da API (Paginação).
        
        :param path: Caminho do endpoint (ex: 'orders' ou 'catalog/products').
        :param params: Parâmetros de busca opcionais.
        :param limit_per_page: Quantidade de registros por página (máximo permitido é 100).
        :return: Um generator que devolve cada item (data) retornado individualmente.
        """
        query_params = params.copy() if params else {}
        query_params["limit"] = min(limit_per_page, 100)
        query_params["page"] = 1

        while True:
            logger.info(f"Buscando página {query_params['page']} do endpoint '{path}'...")
            result = self.request("GET", path, params=query_params)
            
            # Retorna os itens desta página
            items = result.get("data", [])
            for item in items:
                yield item
            
            # Verifica paginação através do bloco "meta" da resposta
            meta = result.get("meta", {}).get("pagination", {})
            current_page = meta.get("current_page", 1)
            total_pages = meta.get("total_pages", 1)
            
            if current_page >= total_pages or not items:
                logger.info(f"Busca finalizada. Total de páginas processadas: {current_page}.")
                break
                
            query_params["page"] += 1

    def get_orders(self, filters: Optional[Dict[str, Any]] = None, 
                   include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Busca os pedidos da loja usando paginação automática.
        
        :param filters: Dicionário com filtros adicionais, ex: {'status_id[]': [2], 'payment_method[]': ['pix']}
                        ou data no formato 'created_at:2024-06-01|2024-06-30'
        :param include: Lista de relações adicionais para incluir na resposta,
                        ex: ['customer', 'items', 'transactions', 'shipping_address']
        :return: Generator com os pedidos.
        """
        params = filters.copy() if filters else {}
        if include:
            params["include"] = ",".join(include)
        
        return self.get_paginated_data("orders", params=params)

    def get_products(self, filters: Optional[Dict[str, Any]] = None, 
                     include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Busca os produtos do catálogo usando paginação automática.
        
        :param filters: Filtros de produtos.
        :param include: Relações adicionais (ex: ['skus', 'images', 'brand', 'categories'])
        :return: Generator com os produtos.
        """
        params = filters.copy() if filters else {}
        if include:
            params["include"] = ",".join(include)
            
        return self.get_paginated_data("catalog/products", params=params)

    def get_abandoned_carts(self, filters: Optional[Dict[str, Any]] = None, 
                            include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Busca os carrinhos abandonados da loja usando paginação automática.
        
        :param filters: Filtros adicionais (ex: busca por período).
        :param include: Relações adicionais (ex: ['customer', 'items'])
        :return: Generator com os carrinhos abandonados.
        """
        params = filters.copy() if filters else {}
        if include:
            params["include"] = ",".join(include)
        
        return self.get_paginated_data("checkout/carts", params=params)

# Demonstração de Uso
if __name__ == "__main__":
    # Para testar localmente, defina as variáveis de ambiente ou altere os valores abaixo:
    USER_TOKEN = os.getenv("YAMPI_USER_TOKEN", "seu-user-token")
    USER_SECRET_KEY = os.getenv("YAMPI_USER_SECRET_KEY", "sua-user-secret-key")
    MERCHANT_ALIAS = os.getenv("YAMPI_MERCHANT_ALIAS", None)  # Opcional
    
    if USER_TOKEN == "seu-user-token" or USER_SECRET_KEY == "sua-user-secret-key":
        print("[AVISO] Por favor, defina suas credenciais da Yampi para executar o teste.")
        print("Você pode defini-las no código ou configurar as variáveis de ambiente:")
        print("export YAMPI_USER_TOKEN='seu-token'")
        print("export YAMPI_USER_SECRET_KEY='sua-secret-key'")
    else:
        print("Iniciando conexão com a API Yampi...")
        client = YampiClient(
            user_token=USER_TOKEN,
            user_secret_key=USER_SECRET_KEY,
            merchant_alias=MERCHANT_ALIAS
        )
        
        # Testando conexão buscando as informações da loja/usuário
        try:
            print(f"Alias resolvido: {client.merchant_alias}")
            
            # Buscar os últimos 5 produtos do catálogo apenas para validação
            print("\nBuscando produtos do catálogo...")
            # Usando limit menor para demonstração rápida
            products_generator = client.get_products(include=["skus"])
            
            counter = 0
            for product in products_generator:
                print(f"- Produto: ID: {product.get('id')} | Nome: {product.get('name')}")
                skus = product.get("skus", {}).get("data", [])
                print(f"  SKUs cadastrados ({len(skus)}):")
                for sku in skus:
                    print(f"    * SKU ID: {sku.get('id')} | Preço Venda: R$ {sku.get('price_sale')}")
                
                counter += 1
                if counter >= 5:
                    print("Demonstração: Limite de 5 produtos alcançado.")
                    break
                    
        except Exception as e:
            print(f"\nOcorreu um erro no teste: {str(e)}")
