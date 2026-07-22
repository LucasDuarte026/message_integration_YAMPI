import logging
import os
import concurrent.futures
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple, Optional

from src.core.config import Config
from src.core.macros import (
    MACRO_TIMEOUT_PAGAMENTO_SEG,
    MACRO_CUPOM_PEDIDO_1_HORAS,
    MACRO_CUPOM_PEDIDO_2_HORAS,
    MACRO_CUPOM_PEDIDO_3_HORAS,
    MACRO_PERDIDO_PEDIDO_HORAS
)
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol

logger = logging.getLogger(__name__)

class OrderProcessor:
    def __init__(
        self, 
        config: Config,
        api_client: YampiClientProtocol,
        message_provider: MessageProviderProtocol,
        state_repo: StateRepositoryProtocol
    ):
        self.config = config
        self.api_client = api_client
        self.message_provider = message_provider
        self.state_repo = state_repo
        
    def process(self) -> None:
        logger.info("Iniciando processamento de pedidos (STG)...")
        
        try:
            orders_generator = self.api_client.get_orders(include=['customer', 'items', 'status'])
            
            eligible_orders = []
            for order in orders_generator:
                should_continue, is_eligible = self._precheck_order(order)
                if is_eligible:
                    eligible_orders.append(order)
                if not should_continue:
                    break
            
            if not eligible_orders:
                logger.info("Nenhum pedido qualificado para processamento nesta rodada.")
                return
                
            if self.config.MAX_WORKERS <= 1: # util no modo debug
                logger.info(f"Modo de DEBUG Síncrono (MAX_WORKERS={self.config.MAX_WORKERS}): Processando {len(eligible_orders)} pedidos um a um...")
                for idx, order in enumerate(eligible_orders, 1):
                    if getattr(self.config, "INTERACTIVE_DEBUG", False):
                        input(f"\n[DEBUG ORDER {idx}/{len(eligible_orders)}] Pressione ENTER para processar o Pedido ID {order.get('id')}...")
                    logger.info(f">>> Processando Pedido {idx}/{len(eligible_orders)}")
                    self._process_order_concurrently(order)
            else:
                logger.info(f"Iniciando processamento assíncrono para {len(eligible_orders)} pedidos com até {self.config.MAX_WORKERS} workers...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                    executor.map(self._process_order_concurrently, eligible_orders)
                
            logger.info("Processamento finalizado.")
        except Exception as e:
            logger.error(f"Erro no processamento concorrente de pedidos: {e}")

    def _precheck_order(self, order: Dict[str, Any]) -> Tuple[bool, bool]:
        created_at_str = order.get('created_at', {}).get('date')
        if not created_at_str:
            return True, False
            
        try:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return True, False
            
        now_utc3 = datetime.utcnow() - timedelta(hours=3)
        days_since_creation = (now_utc3 - created_at).total_seconds() / (3600 * 24)
        if days_since_creation > 14:
            return False, False
            
        return True, True

    def _read_template(self, template_name: str) -> str:
        template_path = os.path.join("src", "templates", "emails", f"{template_name}.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao ler template {template_path}: {e}")
            return ""

    def _get_cart_id(self, order: Dict[str, Any]) -> Optional[str]:
        metadata = order.get('metadata', {}).get('data', [])
        for meta in metadata:
            if meta.get('key') == 'cart_id':
                return meta.get('value')
        return None

    def _process_order_concurrently(self, order: Dict[str, Any]) -> None:
        order_id = str(order.get('id', ''))
        cart_id = self._get_cart_id(order)
        if not cart_id:
            logger.warning(f"[Worker Pedidos] Pedido {order_id} ignorado pois não possui cart_id.")
            return

        created_at_str = order.get('created_at', {}).get('date')
        try:
            data_pedido = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            data_pedido = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")

        customer_data = order.get('customer', {}).get('data', {})
        cpf = customer_data.get('cpf')
        name = customer_data.get('name', 'Cliente').split()[0]
        email = customer_data.get('email')

        # Determinar SKU mais caro
        sku = None
        highest_price = -1
        items_html = ""
        items_raw = order.get("items", {})
        items_list = items_raw.get("data", []) if isinstance(items_raw, dict) else (items_raw if isinstance(items_raw, list) else [])
        
        for item in items_list:
            item_sku = item.get("item_sku") or item.get("sku", {}).get("data", {}).get("sku")
            price = float(item.get("price", 0.0))
            if price > highest_price and item_sku:
                highest_price = price
                sku = item_sku
                
            title = item.get("name") or item.get("title") or "Produto"
            qty = int(item.get("quantity", 1))
            items_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155;"><strong>{title}</strong></td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: center;">{qty}</td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: right;">R$ {price:.2f}</td>
            </tr>
            """

        # FASE 1: LEITURA E VINCULAÇÃO ATÔMICA
        row = self.state_repo.upsert_from_order(cart_id, order_id, data_pedido, cpf, sku)
        if not row:
            return
            
        stg = row.get('stg')

        # FASE 2: PROCESSAMENTO E I/O EXTERNO
        if stg in (1, 3, 8, 95, 96, 97):
            return  # ESTADO TERMINAL, pula
            
        status_id = order.get('status', {}).get('data', {}).get('id')
        alias = order.get('status', {}).get('data', {}).get('alias', '')
        is_paid = status_id == 4 or alias == 'paid'
        is_pending = status_id == 3 or alias == 'waiting_payment'
        
        now_utc3 = datetime.utcnow() - timedelta(hours=3)
        diff_hours = (now_utc3 - data_pedido).total_seconds() / 3600
        diff_seconds = (now_utc3 - data_pedido).total_seconds()

        new_stg = None
        template_name = None
        subject = ""

        if stg is None:
            if diff_seconds <= MACRO_TIMEOUT_PAGAMENTO_SEG:
                if is_paid:
                    new_stg = 1
                    template_name = "email_1_confirmacao_pagamento"
                    subject = f"Pagamento Confirmado: Pedido #{order_id}"
                elif is_pending:
                    new_stg = 2
                    template_name = "email_2_incentivo_pagamento"
                    subject = f"Finalize seu pagamento: Pedido #{order_id}"
            else:
                if not is_paid:
                    new_stg = 4
        elif stg == 2:
            if is_paid:
                new_stg = 3
                template_name = "email_1_confirmacao_pagamento"
                subject = f"Pagamento Confirmado: Pedido #{order_id}"
            elif diff_seconds > MACRO_TIMEOUT_PAGAMENTO_SEG and not is_paid:
                new_stg = 4
        elif stg == 4:
            if diff_hours > MACRO_CUPOM_PEDIDO_1_HORAS:
                new_stg = 5
                template_name = "cupom_1_pedido_10"
                subject = f"10% de desconto para o seu pedido #{order_id}"
        elif stg == 5:
            if diff_hours > MACRO_CUPOM_PEDIDO_2_HORAS:
                new_stg = 6
                template_name = "cupom_2_pedido_15"
                subject = f"15% de desconto para o seu pedido #{order_id}"
        elif stg == 6:
            if diff_hours > MACRO_CUPOM_PEDIDO_3_HORAS:
                new_stg = 7
                template_name = "cupom_3_pedido_20"
                subject = f"20% de desconto! Última chance pedido #{order_id}"
        elif stg == 7:
            if diff_hours > MACRO_PERDIDO_PEDIDO_HORAS:
                new_stg = 8

        if new_stg is not None:
            if template_name and email:
                html_body = self._read_template(template_name)
                if html_body:
                    html_body = html_body.replace("{name}", name)
                    html_body = html_body.replace("{order_id}", order_id)
                    html_body = html_body.replace("{items_html}", items_html)
                    
                    # Salvar HTML localmente
                    folder_path = os.path.join("emails", f"order_{order_id}")
                    file_path = os.path.join(folder_path, f"email_stg_{new_stg}.html")
                    try:
                        os.makedirs(folder_path, exist_ok=True)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(html_body)
                    except Exception as e:
                        logger.error(f"[Worker Pedidos] Falha ao criar HTML para o pedido {order_id}: {e}")

                    recipient_email = self.config.TEST_EMAIL_RECIPIENT  # Em prod, usar `email`
                    self.message_provider.send_email_message(recipient_email, subject, html_body)
                    logger.info(f"[Worker Pedidos] E-mail STG {new_stg} enviado para pedido {order_id}")

            # FASE 3: GRAVAÇÃO ATÔMICA
            self.state_repo.update_stg(cart_id, new_stg)
            logger.info(f"[Worker Pedidos] Estado do cart_id {cart_id} atualizado para STG={new_stg}")
