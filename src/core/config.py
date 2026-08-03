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
    
    # Email Configurations
    TEST_EMAIL_RECIPIENT: str = "deutschlucas026@gmail.com"
    
    # SMTP Configurations (Produção)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    MAX_WORKERS: int = 10
    INTERACTIVE_DEBUG: bool = False
    APP_VERSION: str = "unknown"

def load_config() -> Config:
    """
    Carrega as variáveis de ambiente necessárias e retorna o objeto Config.
    """
    token = os.environ.get("YAMPI_USER_TOKEN")
    secret = os.environ.get("YAMPI_USER_SECRET_KEY")
    
    if not token or not secret:
        raise ValueError("As credenciais YAMPI_USER_TOKEN e YAMPI_USER_SECRET_KEY devem ser configuradas no ambiente.")
        
    version_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            app_version = f.read().strip()
    except Exception:
        app_version = "unknown"
        
    return Config(
        YAMPI_USER_TOKEN=token,
        YAMPI_USER_SECRET_KEY=secret,
        YAMPI_ALIAS=os.environ.get("YAMPI_ALIAS"),
        DATABASE_URL=os.environ.get("DATABASE_URL", "postgresql://postgres:mysecretpassword@localhost:5432/message_integration"),
        TEST_EMAIL_RECIPIENT=os.environ.get("TEST_EMAIL_RECIPIENT", "deutschlucas026@gmail.com"),
        SMTP_HOST=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.environ.get("SMTP_PORT", 587)),
        SMTP_USER=os.environ.get("SMTP_USER"),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD"),
        SMTP_FROM=os.environ.get("SMTP_FROM"),
        MAX_WORKERS=int(os.environ.get("MAX_WORKERS", 10)),
        APP_VERSION=app_version
    )
