import os
from typing import Tuple
from src.domain.events import OrderTransitionEvent, CartTransitionEvent
from src.services.email_builders.base_builder import BaseEmailBuilder

class PaymentConfirmedBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("pedido_aprovado")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("pedido_aprovado", template_data)
        
        # Puxando subject do brand_data.yml
        subject_template = self.brand_data.get("templates_copy", {}).get("pedido_aprovado", {}).get("subject", "Pagamento Confirmado")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class PaymentIncentiveBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("pedido_pendente")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("pedido_pendente", template_data)
        
        subject_template = self.brand_data.get("templates_copy", {}).get("pedido_pendente", {}).get("subject", "Finalize seu pagamento")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template

        return subject, html

class ShippingTrackerBuilder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("pedido_a_caminho")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("pedido_a_caminho", template_data)
        
        subject_template = self.brand_data.get("templates_copy", {}).get("pedido_a_caminho", {}).get("subject", "Seu pedido está a caminho!")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon10Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_pedido", {}).get("cupom_1", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "ELEVE10")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("cupom_pedido_1")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("cupom_pedido_1", template_data)
        
        subject_template = cupom_info.get("subject", "10% de desconto")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon15Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_pedido", {}).get("cupom_2", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "ELEVE15")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("cupom_pedido_2")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("cupom_pedido_2", template_data)
        
        subject_template = cupom_info.get("subject", "15% de desconto")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon20Builder(BaseEmailBuilder):
    def build(self, event: OrderTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_pedido", {}).get("cupom_3", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "ELEVE20")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("cupom_pedido_3")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("cupom_pedido_3", template_data)
        
        subject_template = cupom_info.get("subject", "20% de desconto")
        try:
            subject = subject_template.format(order_number=event.order_number, customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon4CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements_cart(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_carrinho", {}).get("carrinho_cupom4", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "CART10")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("carrinho_abandonado_4")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("carrinho_abandonado_cupom4", template_data)
        
        subject_template = cupom_info.get("subject", "Seu carrinho está esperando")
        try:
            subject = subject_template.format(customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon5CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements_cart(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_carrinho", {}).get("carrinho_cupom5", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "CART15")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("carrinho_abandonado_5")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("carrinho_abandonado_cupom5", template_data)
        
        subject_template = cupom_info.get("subject", "15% OFF no carrinho")
        try:
            subject = subject_template.format(customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html

class Coupon6CartBuilder(BaseEmailBuilder):
    def build(self, event: CartTransitionEvent) -> Tuple[str, str]:
        template_data = self._apply_common_replacements_cart(event)
        cupom_info = self.brand_data.get("templates_copy", {}).get("cupons_carrinho", {}).get("carrinho_cupom6", {})
        template_data["coupon_code"] = cupom_info.get("coupon_code", "CART20")
        template_data["value_cupom"] = str(cupom_info.get("discount", "10")).replace("% OFF", "").strip()
        img_banner = self.brand_data.get("images", {}).get("body_banners", {}).get("carrinho_abandonado_6")
        template_data.setdefault("body_image_url", img_banner)
        html = self.render_template("carrinho_abandonado_cupom6", template_data)
        
        subject_template = cupom_info.get("subject", "20% OFF no carrinho")
        try:
            subject = subject_template.format(customer_name=template_data.get("name", "Cliente"))
        except KeyError:
            subject = subject_template
            
        return subject, html
