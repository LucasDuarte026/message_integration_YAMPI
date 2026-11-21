import os
import logging
from typing import Any, List, Optional, Tuple
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
from src.core.telemetry import (
    capture_email_dispatch_error,
    email_dispatch_scope,
    extract_recipient_domain,
    record_email_dispatch_failed,
    record_email_dispatch_started,
    resolve_email_type,
    sanitize_error_message,
)

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, message_provider, config):
        self.provider = message_provider
        self.config = config

    @staticmethod
    def _extract_cart_id_from_order(order_data: dict) -> Optional[str]:
        """Extrai defensivamente o cart_id presente em `order_data.metadata.data`."""
        if not isinstance(order_data, dict):
            return None
        metadata = order_data.get("metadata")
        if not isinstance(metadata, dict):
            return None
        data_list = metadata.get("data")
        if not isinstance(data_list, list):
            return None
        for item in data_list:
            if isinstance(item, dict) and item.get("key") == "cart_id":
                val = item.get("value")
                if val is not None and str(val).strip():
                    return str(val).strip()
        return None

    def _resolve_recipient_email(self, customer_data: Any) -> Optional[str]:
        """Resolve o destinatário considerando modo homologação e extração defensiva."""
        if macros.MACRO_FORCE_TEST_EMAIL_RECIPIENT:
            test_recipient = getattr(self.config, "TEST_EMAIL_RECIPIENT", None)
            return (
                test_recipient.strip()
                if isinstance(test_recipient, str) and test_recipient.strip()
                else None
            )
        if not isinstance(customer_data, dict):
            return None
        raw_email = customer_data.get("email")
        return raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

    def _build_email_content(
        self,
        builder: Any,
        event: Any,
        *,
        template_name: str,
        email_type: str,
        channel: str,
        recipient_domain: str,
        recipient_email: Optional[str],
        entity_label: str,
    ) -> Optional[Tuple[str, str, Optional[str]]]:
        """Executa o builder de e-mail registrando telemetria completa em caso de falha."""
        try:
            return builder.build_with_plain_text(event)
        except Exception as exc:
            extra_emails: List[str] = []
            customer_data = getattr(event, "customer_data", None)
            if isinstance(customer_data, dict):
                raw_customer_email = customer_data.get("email")
                if isinstance(raw_customer_email, str) and raw_customer_email.strip():
                    extra_emails.append(raw_customer_email.strip())

            sanitized_exc_msg = str(exc)
            for candidate in [recipient_email, *extra_emails]:
                if isinstance(candidate, str) and candidate.strip():
                    sanitized_exc_msg = sanitize_error_message(
                        sanitized_exc_msg, raw_email=candidate
                    )

            record_email_dispatch_started(
                {
                    "email.provider": "template_builder",
                    "email.channel": channel,
                    "email.type": email_type,
                    "email.recipient_domain": recipient_domain,
                }
            )
            record_email_dispatch_failed(
                {
                    "email.provider": "template_builder",
                    "email.channel": channel,
                    "email.type": email_type,
                    "email.recipient_domain": recipient_domain,
                    "email.failure_stage": "template_build",
                    "email.error_type": type(exc).__name__,
                }
            )
            capture_email_dispatch_error(
                exc,
                failure_stage="template_build",
                tags={"email.channel": channel, "email.type": email_type},
                raw_email=recipient_email,
                extra_raw_emails=extra_emails,
            )
            logger.error(
                f"[NotificationService] Falha ao montar template '{template_name}' para {entity_label}: {sanitized_exc_msg}",
                exc_info=exc,
            )
            return None

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

        is_promotional = template_name in {"cupom_pedido_1", "cupom_pedido_2", "cupom_pedido_3"}
        channel = "promotional" if is_promotional else "transactional"
        email_type = resolve_email_type(template_name)
        recipient_email = self._resolve_recipient_email(event.customer_data)
        recipient_domain = extract_recipient_domain(recipient_email)
        cart_id = self._extract_cart_id_from_order(event.order_data)

        primary_sent = False
        with email_dispatch_scope(
            flow="order",
            template_name=template_name,
            stage=f"STG_{event.new_stg}",
            entity_type="order",
            entity_id=str(event.order_id),
            is_promotional=is_promotional,
            dispatch_kind="primary",
            order_number=str(event.order_number),
            cart_id=cart_id,
            recipient_domain=recipient_domain,
            email_type=email_type,
        ):
            content = self._build_email_content(
                builder,
                event,
                template_name=template_name,
                email_type=email_type,
                channel=channel,
                recipient_domain=recipient_domain,
                recipient_email=recipient_email,
                entity_label=f"pedido ID: # {event.order_id}",
            )
            if content is None:
                return False
            subject, html_body, plain_text = content

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

            if recipient_email:
                success = self.provider.send_email_message(
                    recipient_email,
                    subject,
                    html_body,
                    plain_text=plain_text,
                    is_promotional=is_promotional,
                    email_type=email_type,
                )
                if success:
                    logger.info(f"[NotificationService] E-mail STG {event.new_stg} ({template_name}) enviado para pedido ID: # {event.order_id} (Nº {event.order_number})")
                    primary_sent = True
                else:
                    logger.warning(f"[NotificationService] Falha ao enviar e-mail STG {event.new_stg} para pedido ID: # {event.order_id}")
                    return False
            else:
                logger.warning(f"[NotificationService] No recipient email found for order {event.order_id}")
                return False

        # Envio em duplicata (Cópia de acompanhamento/supervisão em produção)
        if (
            primary_sent
            and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH
            and self.config.TEST_EMAIL_RECIPIENT
            and recipient_email != self.config.TEST_EMAIL_RECIPIENT
        ):
            logger.info(f"[NotificationService] [DUPLICATA] Despachando cópia idêntica do pedido #{event.order_number} para: {self.config.TEST_EMAIL_RECIPIENT}")
            with email_dispatch_scope(
                flow="order",
                template_name=template_name,
                stage=f"STG_{event.new_stg}",
                entity_type="order",
                entity_id=str(event.order_id),
                is_promotional=is_promotional,
                dispatch_kind="duplicate",
                order_number=str(event.order_number),
                cart_id=cart_id,
                recipient_domain=extract_recipient_domain(self.config.TEST_EMAIL_RECIPIENT),
                email_type=email_type,
            ):
                self.provider.send_email_message(
                    self.config.TEST_EMAIL_RECIPIENT,
                    subject,
                    html_body,
                    plain_text=plain_text,
                    is_promotional=is_promotional,
                    email_type=email_type,
                )
        return True

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

        channel = "promotional"
        email_type = resolve_email_type(template_name)
        recipient_email = self._resolve_recipient_email(event.customer_data)
        recipient_domain = extract_recipient_domain(recipient_email)

        primary_sent = False
        with email_dispatch_scope(
            flow="abandoned_cart",
            template_name=template_name,
            stage=f"STC_{event.new_stc}",
            entity_type="cart",
            entity_id=str(event.cart_id),
            is_promotional=True,
            dispatch_kind="primary",
            cart_id=str(event.cart_id),
            recipient_domain=recipient_domain,
            email_type=email_type,
        ):
            content = self._build_email_content(
                builder,
                event,
                template_name=template_name,
                email_type=email_type,
                channel=channel,
                recipient_domain=recipient_domain,
                recipient_email=recipient_email,
                entity_label=f"carrinho ID: {event.cart_id}",
            )
            if content is None:
                return False
            subject, html_body, plain_text = content

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

            if recipient_email:
                success = self.provider.send_email_message(
                    recipient_email,
                    subject,
                    html_body,
                    plain_text=plain_text,
                    is_promotional=True,
                    email_type=email_type,
                )
                if success:
                    logger.info(f"[NotificationService] E-mail STC {event.new_stc} ({template_name}) enviado para carrinho ID: {event.cart_id}")
                    primary_sent = True
                else:
                    logger.warning(f"[NotificationService] Falha ao enviar e-mail STC {event.new_stc} para carrinho ID: {event.cart_id}")
                    return False
            else:
                logger.warning(f"[NotificationService] No recipient email found for cart {event.cart_id}")
                return False

        # Envio em duplicata (Cópia de acompanhamento/supervisão em produção)
        if (
            primary_sent
            and macros.MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH
            and self.config.TEST_EMAIL_RECIPIENT
            and recipient_email != self.config.TEST_EMAIL_RECIPIENT
        ):
            logger.info(f"[NotificationService] [DUPLICATA] Despachando cópia idêntica do carrinho {event.cart_id} para: {self.config.TEST_EMAIL_RECIPIENT}")
            with email_dispatch_scope(
                flow="abandoned_cart",
                template_name=template_name,
                stage=f"STC_{event.new_stc}",
                entity_type="cart",
                entity_id=str(event.cart_id),
                is_promotional=True,
                dispatch_kind="duplicate",
                cart_id=str(event.cart_id),
                recipient_domain=extract_recipient_domain(self.config.TEST_EMAIL_RECIPIENT),
                email_type=email_type,
            ):
                self.provider.send_email_message(
                    self.config.TEST_EMAIL_RECIPIENT,
                    subject,
                    html_body,
                    plain_text=plain_text,
                    is_promotional=True,
                    email_type=email_type,
                )
        return True

