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
    DATABASE_URL: str = "postgresql://postgres:mysecretpassword@localhost:5432/message_integration"
    
    # Configurações de Regra de Negócio
    ABANDONED_CART_MINUTES: int = 30
    MESSAGE_1_DELAY_HOURS: int = 2
    MAX_CART_AGE_HOURS: int = 48  # Limite de 2 dias para não processar itens antigos

    # Meta WhatsApp Business Cloud API
    META_WA_TOKEN: Optional[str] = None
    META_PHONE_NUMBER_ID: Optional[str] = None
    META_WA_TEMPLATE_NAME: str = "hello_world"
    META_WA_TEMPLATE_LANG: str = "en_US"

    # Email Configurations
    TEST_EMAIL_RECIPIENT: str = "wpplucas026@gmail.com"
    
    # SMTP Configurations (Produção)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    MAX_WORKERS: int = 10

def load_config() -> Config:
    """
    Carrega as variáveis de ambiente necessárias e retorna o objeto Config.
    """
    token = os.environ.get("YAMPI_USER_TOKEN")
    secret = os.environ.get("YAMPI_USER_SECRET_KEY")
    
    if not token or not secret:
        raise ValueError("As credenciais YAMPI_USER_TOKEN e YAMPI_USER_SECRET_KEY devem ser configuradas no ambiente.")
    return Config(
        YAMPI_USER_TOKEN=token,
        YAMPI_USER_SECRET_KEY=secret,
        YAMPI_ALIAS=os.environ.get("YAMPI_ALIAS"),
        DATABASE_URL=os.environ.get("DATABASE_URL", "postgresql://postgres:mysecretpassword@localhost:5432/message_integration"),
        META_WA_TOKEN=os.environ.get("META_WA_TOKEN"),
        META_PHONE_NUMBER_ID=os.environ.get("META_PHONE_NUMBER_ID"),
        META_WA_TEMPLATE_NAME=os.environ.get("META_WA_TEMPLATE_NAME", "hello_world"),
        META_WA_TEMPLATE_LANG=os.environ.get("META_WA_TEMPLATE_LANG", "en_US"),
        TEST_EMAIL_RECIPIENT=os.environ.get("TEST_EMAIL_RECIPIENT", "wpplucas026@gmail.com"),
        MAX_CART_AGE_HOURS=int(os.environ.get("MAX_CART_AGE_HOURS", 48)),
        SMTP_HOST=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", 587)),
        SMTP_USER=os.environ.get("SMTP_USER"),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD"),
        SMTP_FROM=os.environ.get("SMTP_FROM"),
        MAX_WORKERS=int(os.environ.get("MAX_WORKERS", 10))
    )
