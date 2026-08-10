import unittest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Generator, Optional, List

# Adiciona o diretório raiz do projeto para viabilizar as importações de 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import Config
from src.core import macros
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol
from src.workers.abandoned_cart import AbandonedCartProcessor
from src.core.time_utils import get_now_utc

class MockYampiClient(YampiClientProtocol):
    def __init__(self, carts: List[Dict[str, Any]]):
        self.carts = carts

    def get_orders(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Any:
        return []

    def get_abandoned_carts(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Generator[Dict[str, Any], None, None]:
        for cart in self.carts:
            yield cart

class MockMessageProvider(MessageProviderProtocol):
    def __init__(self):
        self.sent_messages = []

    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        self.sent_messages.append({
            "type": "whatsapp",
            "phone": phone_number,
            "message": message
        })
        return True

    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        self.sent_messages.append({
            "type": "email",
            "email": email,
            "subject": subject,
            "body": html_body
        })
        return True

class MockStateRepository(StateRepositoryProtocol):
    def __init__(self):
        self.stc_map = {}
        self.sent_emails = set()

    def upsert_from_order(self, cart_id: str, order_id: str, order_number: str, data_pedido: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        return None

    def upsert_from_cart(self, cart_id: str, data_carrinho: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        stc = self.stc_map.get(cart_id)
        return {'cart_id': cart_id, 'order_id': None, 'stc': stc}

    def update_stg(self, cart_id: str, new_stg: int) -> None:
        pass

    def update_stc(self, cart_id: str, new_stc: int) -> None:
        self.stc_map[cart_id] = new_stc

    def mark_cart_email_sent(self, cart_id: str, email_type: str, sent_at: datetime) -> None:
        self.sent_emails.add((cart_id, email_type))

    def has_cart_received_email(self, cart_id: str, email_type: str) -> bool:
        return (cart_id, email_type) in self.sent_emails

    def mark_cart_abandoned_72h(self, cart_id: str) -> None:
        self.abandoned_72h.add(cart_id)

    def is_cart_abandoned_72h(self, cart_id: str) -> bool:
        return cart_id in self.abandoned_72h

    def mark_order_email_sent(self, order_id: str, email_type: str, sent_at: datetime) -> None:
        pass

    def has_order_received_email(self, order_id: str, email_type: str) -> bool:
        return False

class TestAbandonedCartProcessor(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            YAMPI_USER_TOKEN="test-token",
            YAMPI_USER_SECRET_KEY="test-secret",
            YAMPI_ALIAS="test-alias",
            TEST_EMAIL_RECIPIENT="teste_destino@exemplo.com"
        )

    def test_process_qualifying_cart(self):
        # 1. Cria um carrinho abandonado há 5 horas (qualifica para a fase 'lembrete', que exige >= 4 horas)
        eighteen_hours_ago = (get_now_utc() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
        carts = [
            {
                "id": "cart_123",
                "created_at": {"date": eighteen_hours_ago, "timezone": "America/Sao_Paulo"},
                "updated_at": {"date": eighteen_hours_ago, "timezone": "America/Sao_Paulo"},
                "recovery_url": "https://checkout.minhaloja.com.br/recupera/123",
                "customer": {
                    "data": {
                        "name": "Luska",
                        "email": "luska@cliente.com"
                    }
                },
                "items": {
                    "data": [
                        {
                            "title": "Fone Bluetooth Premium",
                            "price": 149.90,
                            "quantity": 2
                        }
                    ]
                }
            }
        ]

        client = MockYampiClient(carts)
        provider = MockMessageProvider()
        repo = MockStateRepository()

        processor = AbandonedCartProcessor(self.config, client, provider, repo)
        processor.process()

        # Verifica se o e-mail foi enviado
        expected_count = 2 if (not macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH) else 1
        self.assertEqual(len(provider.sent_messages), expected_count)
        expected_email = "teste_destino@exemplo.com" if macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT else "luska@cliente.com"
        self.assertEqual(provider.sent_messages[0]["email"], expected_email)
        self.assertEqual(provider.sent_messages[0]["subject"], "🛒 Seu carrinho está te esperando — Ganhe 10% OFF para finalizar!")
        
        # Verifica se o HTML gerado contém o link de recuperação
        html_content = provider.sent_messages[0]["body"]
        self.assertIn("https://checkout.minhaloja.com.br/recupera/123", html_content)

    def test_process_recent_cart_ignored(self):
        # 2. Cria um carrinho abandonado há apenas 10 minutos (não qualifica para nenhuma fase)
        ten_minutes_ago = (get_now_utc() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        carts = [
            {
                "id": "cart_456",
                "updated_at": {"date": ten_minutes_ago},
                "customer": {
                    "data": {
                        "name": "Maria",
                        "email": "maria@cliente.com"
                    }
                },
                "items": {
                    "data": [
                        {
                            "title": "Camiseta Geek",
                            "price": 59.90,
                            "quantity": 1
                        }
                    ]
                }
            }
        ]

        client = MockYampiClient(carts)
        provider = MockMessageProvider()
        repo = MockStateRepository()

        processor = AbandonedCartProcessor(self.config, client, provider, repo)
        processor.process()

        # Não deve ter enviado e-mail
        self.assertEqual(len(provider.sent_messages), 0)

    def test_process_duplicate_prevented(self):
        # 3. Cria um carrinho elegível (18 horas atrás) mas que o repositório já marca como STC=15 enviado
        eighteen_hours_ago = (get_now_utc() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
        carts = [
            {
                "id": "cart_789",
                "updated_at": {"date": eighteen_hours_ago},
                "customer": {
                    "data": {
                        "name": "João",
                        "email": "joao@cliente.com"
                    }
                },
                "items": {
                    "data": [
                        {
                            "title": "Teclado Mecânico",
                            "price": 250.00,
                            "quantity": 1
                        }
                    ]
                }
            }
        ]

        client = MockYampiClient(carts)
        provider = MockMessageProvider()
        repo = MockStateRepository()
        
        # Simula envio prévio do e-mail da fase STC 15
        repo.stc_map["cart_789"] = 15

        processor = AbandonedCartProcessor(self.config, client, provider, repo)
        processor.process()

        # Não deve enviar novamente
        self.assertEqual(len(provider.sent_messages), 0)

    def test_process_very_old_cart_stops_loop(self):
        # 4. Cria dois carrinhos: o primeiro é mais antigo que o limite max de 15 dias (400 horas).
        twenty_days_ago = (get_now_utc() - timedelta(hours=400)).strftime("%Y-%m-%d %H:%M:%S")
        eighteen_hours_ago = (get_now_utc() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
        
        carts = [
            {
                "id": "cart_old",
                "updated_at": {"date": twenty_days_ago},
                "customer": {
                    "data": {
                        "name": "Velho",
                        "email": "velho@cliente.com"
                    }
                },
                "items": {
                    "data": [{"title": "Item Velho", "price": 10.0, "quantity": 1}]
                }
            },
            {
                "id": "cart_new",
                "updated_at": {"date": eighteen_hours_ago},
                "customer": {
                    "data": {
                        "name": "Novo",
                        "email": "novo@cliente.com"
                    }
                },
                "items": {
                    "data": [{"title": "Item Novo", "price": 10.0, "quantity": 1}]
                }
            }
        ]

        client = MockYampiClient(carts)
        provider = MockMessageProvider()
        repo = MockStateRepository()

        processor = AbandonedCartProcessor(self.config, client, provider, repo)
        processor.process()

        # Nenhum e-mail deve ter sido enviado
        self.assertEqual(len(provider.sent_messages), 0)

    def test_logging_contains_abandonment_hours_and_rule(self):
        eighteen_hours_ago = (get_now_utc() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
        carts = [
            {
                "id": "cart_log_test",
                "created_at": {"date": eighteen_hours_ago, "timezone": "America/Sao_Paulo"},
                "updated_at": {"date": eighteen_hours_ago, "timezone": "America/Sao_Paulo"},
                "recovery_url": "https://checkout.minhaloja.com.br/recupera/log_test",
                "customer": {
                    "data": {
                        "name": "Luska",
                        "email": "luska@cliente.com"
                    }
                },
                "items": {
                    "data": [
                        {
                            "title": "Fone Bluetooth Premium",
                            "price": 149.90,
                            "quantity": 2
                        }
                    ]
                }
            }
        ]

        client = MockYampiClient(carts)
        provider = MockMessageProvider()
        repo = MockStateRepository()

        processor = AbandonedCartProcessor(self.config, client, provider, repo)
        
        with self.assertLogs("src.workers.abandoned_cart", level="INFO") as log_capture:
            processor.process()
            
        stc_log_found = any(
            "[Worker Carrinhos] Estado do cart_id cart_log_test atualizado para STC=15" in log
            for log in log_capture.output
        )


                
        self.assertTrue(stc_log_found, f"STC update log not found. Logs: {log_capture.output}")

if __name__ == "__main__":
    unittest.main()
