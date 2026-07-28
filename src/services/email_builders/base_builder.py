import os
import yaml
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any
from jinja2 import Environment, FileSystemLoader

from src.domain.events import OrderTransitionEvent, CartTransitionEvent

logger = logging.getLogger(__name__)

class BaseEmailBuilder(ABC):
    def __init__(self):
        self.templates_dir = os.path.join(os.getcwd(), "src", "templates", "emails")
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir), autoescape=True)
        self.brand_data = self._load_brand_data()

    def _load_brand_data(self) -> Dict[str, Any]:
        brand_data_path = os.path.join(self.templates_dir, "brand_data.yml")
        try:
            with open(brand_data_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Erro ao carregar {brand_data_path}: {e}")
            return {}

    def render_template(self, template_name: str, template_data: Dict[str, Any]) -> str:
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            
            # Merge brand data with template data
            context = self.brand_data.copy()
            context.update(template_data)
            
            return template.render(**context)
        except Exception as e:
            logger.error(f"Erro ao renderizar o template {template_name}.html: {e}")
            return ""

    def _build_items_html(self, data: dict) -> str:
        highest_price = -1
        items_html = ""
        items_raw = data.get("items", {})
        items_list = items_raw.get("data", []) if isinstance(items_raw, dict) else (items_raw if isinstance(items_raw, list) else [])
        
        for item in items_list:
            item_sku = item.get("item_sku") or item.get("sku", {}).get("data", {}).get("sku")
            price_raw = item.get("price") or item.get("product_price") or 0.0
            try:
                price = float(price_raw)
            except (ValueError, TypeError):
                price = 0.0
            if price > highest_price and item_sku:
                highest_price = price
                
            title = item.get("name") or item.get("title") or item.get("product_title") or "Produto"
            qty = int(item.get("quantity", 1))
            items_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155;"><strong>{title}</strong></td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: center;">{qty}</td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: right;">R$ {price:.2f}</td>
            </tr>
            """
        return items_html

    def _apply_common_replacements(self, event: OrderTransitionEvent) -> Dict[str, Any]:
        name = event.customer_data.get('name', 'Cliente').split()[0]
        items_html = self._build_items_html(event.order_data)
        
        value_total = float(event.order_data.get('value_total') or event.order_data.get('value_products') or 0.0)
        total_value_str = f"{value_total:.2f}"
        recovery_url = event.order_data.get('checkout_url') or event.order_data.get('public_url') or event.order_data.get('reorder_url') or ""
        
        shipments = event.order_data.get('shipments', {}).get('data', [])
        shipment_data = shipments[0] if isinstance(shipments, list) and len(shipments) > 0 else {}
        
        found_code = (
            event.order_data.get('track_code') or 
            event.order_data.get('tracking_code') or 
            shipment_data.get('track_code') or 
            shipment_data.get('tracking_code')
        )
        
        is_tracking_stg = getattr(event, 'new_stg', None) == 3
        
        if is_tracking_stg:
            if found_code:
                tracking_code = found_code
            else:
                tracking_code = 'Disponível em breve'
                logger.error(
                    f"[RASTREIO OBRIGATÓRIO] Pedido ID: # {event.order_id} (Nº {event.order_number}): "
                    f"Transição para STG 3 (rastreio), mas o código de rastreio não foi encontrado na Yampi."
                )
        else:
            if found_code:
                tracking_code = found_code
            else:
                tracking_code = 'Aguardando envio'
                logger.debug(
                    f"[RASTREIO] Pedido ID: # {event.order_id} (Nº {event.order_number}): "
                    f"Código de rastreio ausente no STG={getattr(event, 'new_stg', None)} (esperado). Definido como 'Aguardando envio'."
                )
        
        tracking_url = (
            event.order_data.get('track_url') or 
            event.order_data.get('tracking_url') or 
            shipment_data.get('track_url') or 
            shipment_data.get('tracking_url') or 
            recovery_url or
            'https://eleveme.com.br'
        )

        return {
            "name": name,
            "customer_name": name,
            "order_id": event.order_number,
            "order_number": event.order_number,
            "items_html": items_html,
            "total_value": total_value_str,
            "recovery_url": recovery_url,
            "checkout_url": recovery_url,
            "simulate_url": recovery_url,
            "tracking_code": tracking_code,
            "tracking_url": tracking_url,
            "header_image_url": self.brand_data.get("header_image_url"),
            "whatsapp_icon_url": self.brand_data.get("whatsapp_icon_url"),
            "contact_mail_icon_url": self.brand_data.get("contact_mail_icon_url"),
            "instagram_icon_url": self.brand_data.get("instagram_icon_url"),
            "facebook_icon_url": self.brand_data.get("facebook_icon_url")
        }

    def _apply_common_replacements_cart(self, event: CartTransitionEvent) -> Dict[str, Any]:
        name = event.customer_data.get('name', 'Cliente').split()[0]
        items_html = self._build_items_html(event.cart_data)
        
        value_total = float(event.cart_data.get('value_total') or event.cart_data.get('value_products') or 0.0)
        total_value_str = f"{value_total:.2f}"
        recovery_url = event.cart_data.get("simulate_url") or event.cart_data.get("recovery_url") or event.cart_data.get("checkout_url") or "https://yampi.com.br"
        
        return {
            "name": name,
            "customer_name": name,
            "items_html": items_html,
            "total_value": total_value_str,
            "recovery_url": recovery_url,
            "checkout_url": recovery_url,
            "simulate_url": recovery_url,
            "order_number": None,
            "header_image_url": self.brand_data.get("header_image_url"),
            "whatsapp_icon_url": self.brand_data.get("whatsapp_icon_url"),
            "contact_mail_icon_url": self.brand_data.get("contact_mail_icon_url"),
            "instagram_icon_url": self.brand_data.get("instagram_icon_url"),
            "facebook_icon_url": self.brand_data.get("facebook_icon_url")
        }

    @abstractmethod
    def build(self, event) -> Tuple[str, str]:
        """Returns (subject, html_body)"""
        pass
