import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Generator, Optional, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import Config
from src.core import macros
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol
from src.workers.orders import OrderProcessor
from src.core.time_utils import get_now_utc

class MockOrderYampiClient(YampiClientProtocol):
    def __init__(self, orders: List[Dict[str, Any]]):
        self.orders = orders

    def get_orders(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        for order in self.orders:
            yield order

    def get_abandoned_carts(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Any:
        return []

class MockOrderMessageProvider(MessageProviderProtocol):
    def __init__(self):
        self.sent_messages = []

    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        self.sent_messages.append({"type": "whatsapp", "phone": phone_number, "message": message})
        return True

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        self.sent_messages.append({"type": "email", "email": email, "subject": subject, "body": html_body})
        return True

class MockOrderStateRepository(StateRepositoryProtocol):
    def __init__(self, initial_stg: Optional[int] = None):
        self.stg_map = {}
        self.initial_stg = initial_stg

    def upsert_from_order(self, cart_id: str, order_id: str, order_number: str, data_pedido: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        stg = self.stg_map.get(cart_id, self.initial_stg)
        return {'cart_id': cart_id, 'order_id': order_id, 'stg': stg}

    def upsert_from_cart(self, cart_id: str, data_carrinho: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        return None

    def update_stg(self, cart_id: str, new_stg: int) -> None:
        self.stg_map[cart_id] = new_stg

    def update_stc(self, cart_id: str, new_stc: int) -> None:
        pass

class TestOrderProcessorTrackingValidation(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            YAMPI_USER_TOKEN="test-token",
            YAMPI_USER_SECRET_KEY="test-secret",
            YAMPI_ALIAS="test-alias",
            TEST_EMAIL_RECIPIENT="teste_destino@exemplo.com",
            MAX_WORKERS=1
        )
        self.now_str = (get_now_utc() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    def test_paid_without_tracking_code_remains_in_stg2(self):
        order = {
            "id": "100",
            "number": "1000",
            "created_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "updated_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "status": {"data": {"id": 4, "alias": "paid", "name": "Pagamento aprovado"}},
            "metadata": {"data": [{"key": "cart_id", "value": "cart_101"}]},
            "customer": {"data": {"name": "Luska", "email": "luska@teste.com", "cpf": "12345678900"}},
            "items": {"data": [{"item_sku": "SKU-1", "price": 100.0}]},
            "shipments": {"data": []}
        }
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=2)

        processor = OrderProcessor(self.config, client, provider, repo)
        processor.process()

        self.assertNotIn("cart_101", repo.stg_map)
        self.assertEqual(len(provider.sent_messages), 0)

    def test_paid_with_tracking_code_transitions_to_stg3(self):
        order = {
            "id": "102",
            "number": "1002",
            "created_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "updated_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "status": {"data": {"id": 4, "alias": "paid", "name": "Pagamento aprovado"}},
            "metadata": {"data": [{"key": "cart_id", "value": "cart_102"}]},
            "customer": {"data": {"name": "Luska", "email": "luska@teste.com", "cpf": "12345678900"}},
            "items": {"data": [{"item_sku": "SKU-1", "price": 100.0}]},
            "shipments": {"data": [{"tracking_code": "BR123456789BR"}]}
        }
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=2)

        processor = OrderProcessor(self.config, client, provider, repo)
        processor.process()

        expected_count = 2 if (not macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH) else 1
        self.assertEqual(repo.stg_map.get("cart_102"), 3)
        self.assertEqual(len(provider.sent_messages), expected_count)

    def test_on_carriage_without_tracking_code_remains_null(self):
        order = {
            "id": "103",
            "number": "1003",
            "created_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "updated_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "status": {"data": {"id": 7, "alias": "on_carriage", "name": "Em transporte"}},
            "metadata": {"data": [{"key": "cart_id", "value": "cart_103"}]},
            "customer": {"data": {"name": "Luska", "email": "luska@teste.com", "cpf": "12345678900"}},
            "items": {"data": [{"item_sku": "SKU-1", "price": 100.0}]},
            "shipments": {"data": []}
        }
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        processor = OrderProcessor(self.config, client, provider, repo)
        processor.process()

        self.assertNotIn("cart_103", repo.stg_map)
        self.assertEqual(len(provider.sent_messages), 0)

    def test_on_carriage_with_tracking_code_transitions_to_stg3(self):
        order = {
            "id": "104",
            "number": "1004",
            "created_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "updated_at": {"date": self.now_str, "timezone": "America/Sao_Paulo"},
            "status": {"data": {"id": 7, "alias": "on_carriage", "name": "Em transporte"}},
            "metadata": {"data": [{"key": "cart_id", "value": "cart_104"}]},
            "customer": {"data": {"name": "Luska", "email": "luska@teste.com", "cpf": "12345678900"}},
            "items": {"data": [{"item_sku": "SKU-1", "price": 100.0}]},
            "shipments": {"data": [{"tracking_code": "BR987654321BR"}]}
        }
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        processor = OrderProcessor(self.config, client, provider, repo)
        processor.process()

        expected_count = 2 if (not macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH) else 1
        self.assertEqual(repo.stg_map.get("cart_104"), 3)
        self.assertEqual(len(provider.sent_messages), expected_count)

    def test_email_renders_product_table_from_mock(self):
        import json
        with open("project_decisions/estudos/yampi_api/pedidos.json", "r", encoding="utf-8") as f:
            mock_orders = json.load(f)
        
        # Select first mock order which matches the assertions
        order = mock_orders["data"][0]
        order["created_at"] = {"date": self.now_str, "timezone": "America/Sao_Paulo"}
        order["updated_at"] = {"date": self.now_str, "timezone": "America/Sao_Paulo"}
        order["shipments"] = {"data": [{"tracking_code": "BR123456789BR"}]}
        
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        processor = OrderProcessor(self.config, client, provider, repo)
        processor.process()

        expected_count = 2 if (not macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH) else 1
        self.assertEqual(len(provider.sent_messages), expected_count)
        email_body = provider.sent_messages[0]["body"]
        self.assertIn("Palmilha Eleveme 5 cm", email_body)
        self.assertIn("R$ 87.90", email_body)

if __name__ == "__main__":
    unittest.main()

