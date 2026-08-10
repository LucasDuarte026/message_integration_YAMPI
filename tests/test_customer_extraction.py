import unittest
import sys
import os
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.workers.orders import OrderProcessor
from src.workers.abandoned_cart import AbandonedCartProcessor

class TestCustomerDataExtraction(unittest.TestCase):
    def setUp(self):
        self.order_processor = OrderProcessor.__new__(OrderProcessor)
        self.cart_processor = AbandonedCartProcessor.__new__(AbandonedCartProcessor)

    def test_extract_customer_data_nested(self):
        payload = {
            "customer": {
                "data": {
                    "name": " Ana Clara ",
                    "email": " ana@exemplo.com ",
                    "cpf": "12345678900"
                }
            }
        }
        extracted_order = self.order_processor._extract_customer_data(payload)
        extracted_cart = self.cart_processor._extract_customer_data(payload)

        self.assertEqual(extracted_order.get("email"), " ana@exemplo.com ")
        self.assertEqual(extracted_cart.get("email"), " ana@exemplo.com ")

    def test_extract_customer_data_flat(self):
        payload = {
            "customer": {
                "name": "Carlos",
                "email": "carlos@exemplo.com"
            }
        }
        extracted = self.order_processor._extract_customer_data(payload)
        self.assertEqual(extracted.get("email"), "carlos@exemplo.com")

    def test_extract_customer_data_null(self):
        payload = {"customer": None}
        extracted_order = self.order_processor._extract_customer_data(payload)
        extracted_cart = self.cart_processor._extract_customer_data(payload)

        self.assertEqual(extracted_order, {})
        self.assertEqual(extracted_cart, {})

    def test_extract_customer_data_missing(self):
        payload = {}
        extracted_order = self.order_processor._extract_customer_data(payload)
        extracted_cart = self.cart_processor._extract_customer_data(payload)

        self.assertEqual(extracted_order, {})
        self.assertEqual(extracted_cart, {})

if __name__ == "__main__":
    unittest.main()
