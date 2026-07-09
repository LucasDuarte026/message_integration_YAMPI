import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """
    Configuração base da aplicação.
    As credenciais devem vir do ambiente ou do arquivo .env.
    NUNCA hardcode senhas ou tokens aqui.
    """
    YAMPI_USER_TOKEN: str
    YAMPI_USER_SECRET_KEY: str
    YAMPI_ALIAS: Optional[str] = None
    
    # DB configuration
    SQLITE_DB_PATH: str = "state.db"
    
    # Configurações de Regra de Negócio
    ABANDONED_CART_MINUTES: int = 30
    MESSAGE_1_DELAY_HOURS: int = 2

def load_config() -> Config:
    """
    Carrega as variáveis de ambiente necessárias e retorna o objeto Config.
    Em um cenário real, podemos usar uma biblioteca como python-dotenv
    para carregar do arquivo `.env` para as variáveis de ambiente antes disso.
    """
    token = os.environ.get("YAMPI_USER_TOKEN")
    secret = os.environ.get("YAMPI_USER_SECRET_KEY")
    
    if not token or not secret:
        raise ValueError("As credenciais YAMPI_USER_TOKEN e YAMPI_USER_SECRET_KEY devem ser configuradas no ambiente.")
        
    return Config(
        YAMPI_USER_TOKEN=token,
        YAMPI_USER_SECRET_KEY=secret,
        YAMPI_ALIAS=os.environ.get("YAMPI_ALIAS"),
        SQLITE_DB_PATH=os.environ.get("SQLITE_DB_PATH", "state.db")
    )

# Configuração global que será carregada apenas no momento certo, 
# se importada por arquivos que precisem dela em tempo de execução.
