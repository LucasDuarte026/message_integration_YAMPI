import os
import logging
from src.domain.events import OrderTransitionEvent, CartTransitionEvent
from src.services.email_builders.concrete_builders import (
    PaymentConfirmedBuilder,
    PaymentIncentiveBuilder,
    ShippingTrackerBuilder,
    Coupon10Builder,
    Coupon15Builder,
    Coupon20Builder,
    Coupon4CartBuilder,
    Coupon5CartBuilder,
    Coupon6CartBuilder
)

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, message_provider, config):
        self.provider = message_provider
        self.config = config
        
    def handle_transition(self, event: OrderTransitionEvent, template_name: str) -> None:
        builders = {
            "pedido_aprovado": PaymentConfirmedBuilder(),
            "pedido_pendente": PaymentIncentiveBuilder(),
            "pedido_a_caminho": ShippingTrackerBuilder(),
            "cupom_pedido_1": Coupon10Builder(),
            "cupom_pedido_2": Coupon15Builder(),
            "cupom_pedido_3": Coupon20Builder(),
        }
        
        builder = builders.get(template_name)
        if not builder:
            logger.warning(f"No builder found for template {template_name}")
            return
            
        subject, html_body = builder.build(event)
        
        # Save HTML locally for debugging
        folder_path = os.path.join("emails", f"order_{event.order_id}")
        file_path = os.path.join(folder_path, f"email_stg_{event.new_stg}.html")
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_body)
        except Exception as e:
            logger.error(f"[NotificationService] Falha ao criar HTML para o pedido ID: # {event.order_id} (Nº {event.order_number}): {e}")

        recipient_email = self.config.TEST_EMAIL_RECIPIENT  # Em prod, usar email real
        if not recipient_email:
             recipient_email = event.customer_data.get('email')

        if recipient_email:
            self.provider.send_email_message(recipient_email, subject, html_body)
            logger.info(f"[NotificationService] E-mail STG {event.new_stg} ({template_name}) enviado para pedido ID: # {event.order_id} (Nº {event.order_number})")
        else:
            logger.warning(f"[NotificationService] No recipient email found for order {event.order_id}")

    def handle_cart_transition(self, event: CartTransitionEvent, template_name: str) -> None:
        builders = {
            "carrinho_abandonado_cupom4": Coupon4CartBuilder(),
            "carrinho_abandonado_cupom5": Coupon5CartBuilder(),
            "carrinho_abandonado_cupom6": Coupon6CartBuilder(),
        }
        builder = builders.get(template_name)
        if not builder:
            logger.warning(f"No builder found for cart template {template_name}")
            return
            
        subject, html_body = builder.build(event)
        
        # Save HTML locally for debugging
        folder_path = os.path.join("emails", f"cart_{event.cart_id}")
        file_path = os.path.join(folder_path, f"email_stc_{event.new_stc}.html")
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_body)
        except Exception as e:
            logger.error(f"[NotificationService] Falha ao criar HTML para o carrinho ID: {event.cart_id}: {e}")

        recipient_email = self.config.TEST_EMAIL_RECIPIENT
        if not recipient_email:
             recipient_email = event.customer_data.get('email')

        if recipient_email:
            self.provider.send_email_message(recipient_email, subject, html_body)
            logger.info(f"[NotificationService] E-mail STC {event.new_stc} ({template_name}) enviado para carrinho ID: {event.cart_id}")
        else:
            logger.warning(f"[NotificationService] No recipient email found for cart {event.cart_id}")

