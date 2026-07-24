from typing import Tuple
from src.domain.events import OrderTransitionEvent, CartTransitionEvent
from src.services.email_builders.base_builder import BaseEmailBuilder

class PaymentConfirmedBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("email_1_confirmacao_pagamento")
        html = self._apply_common_replacements(template, event)
        subject = f"Pagamento Confirmado: Pedido # {event.order_number}"
        return subject, html

class PaymentIncentiveBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("email_2_incentivo_pagamento")
        html = self._apply_common_replacements(template, event)
        subject = f"Finalize seu pagamento: Pedido # {event.order_number}"
        return subject, html

class ShippingTrackerBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("envio_rastreio")
        html = self._apply_common_replacements(template, event)
        subject = f"Seu pedido #{event.order_number} está a caminho!"
        return subject, html

class Coupon10Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_1_pedido_10")
        html = self._apply_common_replacements(template, event)
        subject = f"10% de desconto para o seu pedido # {event.order_number}"
        return subject, html

class Coupon15Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_2_pedido_15")
        html = self._apply_common_replacements(template, event)
        subject = f"15% de desconto para o seu pedido # {event.order_number}"
        return subject, html

class Coupon20Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_3_pedido_20")
        html = self._apply_common_replacements(template, event)
        subject = f"20% de desconto! Última chance pedido # {event.order_number}"
        return subject, html

class Coupon4CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_4_carrinho")
        html = self._apply_common_replacements_cart(template, event)
        name = event.customer_data.get('name', 'Cliente').split()[0]
        subject = f"{name}, seu carrinho está te esperando!"
        return subject, html

class Coupon5CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_5_carrinho")
        html = self._apply_common_replacements_cart(template, event)
        name = event.customer_data.get('name', 'Cliente').split()[0]
        subject = f"{name}, ganhe um desconto especial nos seus itens!"
        return subject, html

class Coupon6CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template = self._read_template("cupom_6_carrinho")
        html = self._apply_common_replacements_cart(template, event)
        name = event.customer_data.get('name', 'Cliente').split()[0]
        subject = f"Última chance, {name}! Mega desconto no seu carrinho"
        return subject, html
