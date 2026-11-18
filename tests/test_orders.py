import unittest
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Generator, Optional, List
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import Config
from src.core import macros
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol
from src.workers.orders import OrderProcessor
from src.core.time_utils import get_now_utc, to_local_sp

class MockOrderYampiClient(YampiClientProtocol):
    def __init__(self, orders: List[Dict[str, Any]]):
        self.orders = orders
        self.last_include = None

    def get_orders(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        self.last_include = include
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
        self.data_pedido_map = {}
        self.initial_stg = initial_stg

    def upsert_from_order(self, cart_id: str, order_id: str, order_number: str, data_pedido: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        stg = self.stg_map.get(cart_id, self.initial_stg)
        # Simula coluna TIMESTAMP naive em UTC do PostgreSQL com proteção LEAST
        incoming_naive = (
            data_pedido.astimezone(timezone.utc).replace(tzinfo=None)
            if data_pedido.tzinfo is not None
            else data_pedido
        )
        if cart_id in self.data_pedido_map:
            self.data_pedido_map[cart_id] = min(self.data_pedido_map[cart_id], incoming_naive)
        else:
            self.data_pedido_map[cart_id] = incoming_naive
        return {
            'cart_id': cart_id,
            'order_id': order_id,
            'stg': stg,
            'data_pedido': self.data_pedido_map[cart_id],
        }

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

    def _criar_pedido_base(self, order_id: str, cart_id: str, alias: str, status_id: int, created_dt_utc: datetime, updated_dt_utc: Optional[datetime] = None, tracking_code: Optional[str] = None) -> Dict[str, Any]:
        """Monta payload realista de pedido Yampi com timezone America/Sao_Paulo."""
        created_str = to_local_sp(created_dt_utc).strftime("%Y-%m-%d %H:%M:%S")
        updated_str = to_local_sp(updated_dt_utc or created_dt_utc).strftime("%Y-%m-%d %H:%M:%S")
        shipments = [{"tracking_code": tracking_code}] if tracking_code else []
        return {
            "id": order_id,
            "number": f"NUM-{order_id}",
            "created_at": {"date": created_str, "timezone": "America/Sao_Paulo"},
            "updated_at": {"date": updated_str, "timezone": "America/Sao_Paulo"},
            "status": {"data": {"id": status_id, "alias": alias, "name": alias}},
            "metadata": {"data": [{"key": "cart_id", "value": cart_id}]},
            "customer": {"data": {"name": "Luska Teste", "email": "luska@teste.com", "cpf": "12345678900"}},
            "items": {"data": [{"item_sku": "SKU-1", "price": 100.0}]},
            "shipments": {"data": shipments},
        }

    def test_get_orders_includes_shipments_and_transactions(self):
        """Verifica que o worker solicita shipments e transactions no include da API Yampi."""
        order = self._criar_pedido_base("200", "cart_200", "waiting_payment", 3, get_now_utc() - timedelta(minutes=1))
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository()

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(client.last_include, ["customer", "items", "status", "shipments", "transactions"])

    def test_order_uses_persisted_row_data_pedido_ignoring_newer_updated_at(self):
        """Garante que o worker usa data_pedido persistida (naive UTC) mesmo se updated_at for mais recente."""
        agora_utc = get_now_utc()
        # Banco já tem o registro criado há 25h (naive UTC), em STG=4
        order = self._criar_pedido_base(
            "201",
            "cart_201",
            "cancelled",
            8,
            created_dt_utc=agora_utc - timedelta(minutes=10),
            updated_dt_utc=agora_utc - timedelta(minutes=5),
        )
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=4)
        repo.data_pedido_map["cart_201"] = (agora_utc - timedelta(hours=25)).replace(tzinfo=None)

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(repo.stg_map.get("cart_201"), 5)
        self.assertGreaterEqual(len(provider.sent_messages), 1)

    def test_paid_order_from_null_transitions_to_stg1(self):
        """Pedido aprovado na primeira verificação deve transitar de None para STG=1."""
        order = self._criar_pedido_base("202", "cart_202", "paid", 4, get_now_utc() - timedelta(minutes=2))
        client = MockOrderYampiClient([order])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(repo.stg_map.get("cart_202"), 1)
        self.assertGreaterEqual(len(provider.sent_messages), 1)

    def test_pending_order_before_and_after_5m_delay(self):
        """PIX pendente antes de 5 min aguarda; após 5 min e dentro de 30 min transita para STG=2."""
        agora_utc = get_now_utc()
        order_recente = self._criar_pedido_base("203", "cart_203", "waiting_payment", 3, agora_utc - timedelta(minutes=2))
        order_elegivel = self._criar_pedido_base("204", "cart_204", "waiting_payment", 3, agora_utc - timedelta(minutes=10))

        client = MockOrderYampiClient([order_recente, order_elegivel])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertNotIn("cart_203", repo.stg_map)
        self.assertEqual(repo.stg_map.get("cart_204"), 2)
        self.assertGreaterEqual(len(provider.sent_messages), 1)

    def test_unpaid_order_after_30m_transitions_null_to_stg4_and_stg2_to_stg4(self):
        """Pedidos não pagos após 30 minutos devem transitar para STG=4 sem disparar e-mail."""
        agora_utc = get_now_utc()
        order_from_null = self._criar_pedido_base("205", "cart_205", "waiting_payment", 3, agora_utc - timedelta(minutes=40))
        order_from_2 = self._criar_pedido_base("206", "cart_206", "cancelled", 8, agora_utc - timedelta(minutes=45))

        client = MockOrderYampiClient([order_from_null, order_from_2])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)
        repo.stg_map["cart_206"] = 2

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(repo.stg_map.get("cart_205"), 4)
        self.assertEqual(repo.stg_map.get("cart_206"), 4)
        self.assertEqual(len(provider.sent_messages), 0)

    def test_coupon_progression_stg4_to_5_to_6_to_7_to_8(self):
        """Valida toda a régua temporal de cupons e expiração final: 4->5 (24h), 5->6 (48h), 6->7 (72h), 7->8 (96h)."""
        agora_utc = get_now_utc()
        cenarios = [
            ("207", "cart_207", 4, 25, 5, True),
            ("208", "cart_208", 5, 49, 6, True),
            ("209", "cart_209", 6, 73, 7, True),
            ("210", "cart_210", 7, 97, 8, False),
        ]
        for order_id, cart_id, stg_atual, horas, stg_esperado, envia_email in cenarios:
            with self.subTest(stg_atual=stg_atual, stg_esperado=stg_esperado):
                order = self._criar_pedido_base(order_id, cart_id, "waiting_payment", 3, agora_utc - timedelta(hours=horas))
                client = MockOrderYampiClient([order])
                provider = MockOrderMessageProvider()
                repo = MockOrderStateRepository(initial_stg=stg_atual)

                OrderProcessor(self.config, client, provider, repo).process()

                self.assertEqual(repo.stg_map.get(cart_id), stg_esperado)
                if envia_email:
                    self.assertGreaterEqual(len(provider.sent_messages), 1)
                else:
                    self.assertEqual(len(provider.sent_messages), 0)

    def test_refunded_and_terminal_states(self):
        """Pedido reembolsado vai para STG=8; estados terminais (3, 8, 95) são ignorados."""
        agora_utc = get_now_utc()
        order_refunded = self._criar_pedido_base("211", "cart_211", "refunded", 12, agora_utc - timedelta(hours=1))
        order_terminal = self._criar_pedido_base("212", "cart_212", "paid", 4, agora_utc - timedelta(hours=1))

        client = MockOrderYampiClient([order_refunded, order_terminal])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=1)
        repo.stg_map["cart_212"] = 3

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(repo.stg_map.get("cart_211"), 8)
        self.assertEqual(repo.stg_map.get("cart_212"), 3)
        self.assertEqual(len(provider.sent_messages), 0)

    def test_order_created_at_priority_and_invalid_inputs(self):
        """Valida prioridade de created_at sobre updated_at, falha no SMTP abortando STG e pedidos inválidos."""
        agora_utc = get_now_utc()
        # created_at tem 10 minutos (STG=2), mas updated_at tem 2 horas
        order_prio = self._criar_pedido_base(
            "213",
            "cart_213",
            "waiting_payment",
            3,
            created_dt_utc=agora_utc - timedelta(minutes=10),
            updated_dt_utc=agora_utc - timedelta(hours=2),
        )
        # Pedido sem cart_id e pedido com timezone inválido
        order_sem_cart = {"id": "214", "number": "214", "created_at": order_prio["created_at"], "metadata": {"data": []}}
        order_tz_err = {"id": "215", "number": "215", "created_at": {"date": "2026-08-09 10:00:00", "timezone": "Invalido/TZ"}, "metadata": {"data": [{"key": "cart_id", "value": "cart_215"}]}}
        # Pedido antigo (> 15 dias) encerra iteração
        order_antigo = self._criar_pedido_base("216", "cart_216", "waiting_payment", 3, agora_utc - timedelta(days=20))
        order_apos_antigo = self._criar_pedido_base("217", "cart_217", "paid", 4, agora_utc - timedelta(minutes=2))

        client = MockOrderYampiClient([order_prio, order_sem_cart, order_tz_err, order_antigo, order_apos_antigo])
        provider = MockOrderMessageProvider()
        repo = MockOrderStateRepository(initial_stg=None)

        OrderProcessor(self.config, client, provider, repo).process()

        self.assertEqual(repo.stg_map.get("cart_213"), 2)
        self.assertNotIn("cart_215", repo.stg_map)
        self.assertNotIn("cart_217", repo.stg_map)

        # Se envio de e-mail falhar, transição STG não pode ser gravada
        provider_falha = MockOrderMessageProvider()
        provider_falha.send_email_message = lambda *args, **kwargs: False
        repo_falha = MockOrderStateRepository(initial_stg=None)
        OrderProcessor(self.config, MockOrderYampiClient([order_prio]), provider_falha, repo_falha).process()
        self.assertNotIn("cart_213", repo_falha.stg_map)

if __name__ == "__main__":
    unittest.main()

