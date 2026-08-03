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
from src.core import macros

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, message_provider, config):
        self.provider = message_provider
        self.config = config
        
    def handle_transition(self, event: OrderTransitionEvent, template_name: str) -> bool:
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
            return False
            
        subject, html_body = builder.build(event)
        
        # Save HTML locally for debugging se habilitado
        if macros.MACRO_ENABLE_LOCAL_HTML_SAVING:
            folder_path = os.path.join("local_data/emails", f"order_{event.order_id}")
            file_path = os.path.join(folder_path, f"email_stg_{event.new_stg}.html")
            try:
                os.makedirs(folder_path, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_body)
                logger.info(f"[NotificationService] HTML salvo em: file://{os.path.abspath(file_path)}")
            except Exception as e:
                logger.error(f"[NotificationService] Falha ao criar HTML para o pedido ID: # {event.order_id} (Nº {event.order_number}): {e}")

        if macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT:
            recipient_email = self.config.TEST_EMAIL_RECIPIENT
        else:
            raw_email = event.customer_data.get('email')
            recipient_email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

        if recipient_email:
            success = self.provider.send_email_message(recipient_email, subject, html_body)
            if success:
                logger.info(f"[NotificationService] E-mail STG {event.new_stg} ({template_name}) enviado para pedido ID: # {event.order_id} (Nº {event.order_number})")
                
                # Envio em duplicata (Cópia de acompanhamento/supervisão em produção)
                if macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH and self.config.TEST_EMAIL_RECIPIENT and recipient_email != self.config.TEST_EMAIL_RECIPIENT:
                    logger.info(f"[NotificationService] [DUPLICATA] Despachando cópia idêntica do pedido #{event.order_number} para: {self.config.TEST_EMAIL_RECIPIENT}")
                    self.provider.send_email_message(self.config.TEST_EMAIL_RECIPIENT, subject, html_body)
                return True
            else:
                logger.error(f"[NotificationService] Falha ao enviar e-mail STG {event.new_stg} para pedido ID: # {event.order_id}")
                return False
        else:
            logger.warning(f"[NotificationService] No recipient email found for order {event.order_id}")
            return False

    def handle_cart_transition(self, event: CartTransitionEvent, template_name: str) -> bool:
        builders = {
            "carrinho_abandonado_cupom4": Coupon4CartBuilder(),
            "carrinho_abandonado_cupom5": Coupon5CartBuilder(),
            "carrinho_abandonado_cupom6": Coupon6CartBuilder(),
        }
        builder = builders.get(template_name)
        if not builder:
            logger.warning(f"No builder found for cart template {template_name}")
            return False
            
        subject, html_body = builder.build(event)
        
        # Save HTML locally for debugging se habilitado
        if macros.MACRO_ENABLE_LOCAL_HTML_SAVING:
            folder_path = os.path.join("local_data/emails", f"cart_{event.cart_id}")
            file_path = os.path.join(folder_path, f"email_stc_{event.new_stc}.html")
            try:
                os.makedirs(folder_path, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_body)
                logger.info(f"[NotificationService] HTML de carrinho salvo em: file://{os.path.abspath(file_path)}")
            except Exception as e:
                logger.error(f"[NotificationService] Falha ao criar HTML para o carrinho ID: {event.cart_id}: {e}")


        if macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT:
            recipient_email = self.config.TEST_EMAIL_RECIPIENT
        else:
            raw_email = event.customer_data.get('email')
            recipient_email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

        if recipient_email:
            success = self.provider.send_email_message(recipient_email, subject, html_body)
            if success:
                logger.info(f"[NotificationService] E-mail STC {event.new_stc} ({template_name}) enviado para carrinho ID: {event.cart_id}")
                
                # Envio em duplicata (Cópia de acompanhamento/supervisão em produção)
                if macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH and self.config.TEST_EMAIL_RECIPIENT and recipient_email != self.config.TEST_EMAIL_RECIPIENT:
                    logger.info(f"[NotificationService] [DUPLICATA] Despachando cópia idêntica do carrinho {event.cart_id} para: {self.config.TEST_EMAIL_RECIPIENT}")
                    self.provider.send_email_message(self.config.TEST_EMAIL_RECIPIENT, subject, html_body)
                return True
            else:
                logger.error(f"[NotificationService] Falha ao enviar e-mail STC {event.new_stc} para carrinho ID: {event.cart_id}")
                return False
        else:
            logger.warning(f"[NotificationService] No recipient email found for cart {event.cart_id}")
            return False

