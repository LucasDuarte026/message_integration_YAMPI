import pytest
import os

# Defina as credenciais falsas no ambiente antes de carregar os módulos
os.environ["YAMPI_USER_TOKEN"] = "mock-token-123"
os.environ["YAMPI_USER_SECRET_KEY"] = "mock-secret-456"

@pytest.fixture(scope="session")
def setup_env():
    """
    Fixture global que garante que o ambiente está limpo ou 
    mockado para os testes rodarem sem depender de variáveis reais do .env.
    """
    pass

@pytest.fixture
def mock_yampi_cart_payload():
    """
    Exemplo de payload base da Yampi para carrinhos.
    """
    return {
        "data": [
            {
                "id": 123456,
                "customer": {"cpf": "12345678901", "email": "test@test.com"},
                "items": [{"sku": "PROD-01"}]
            }
        ]
    }
