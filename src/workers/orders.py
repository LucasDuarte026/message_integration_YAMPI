import logging
import os
import concurrent.futures
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple, Optional

from src.core.config import Config
from src.core.macros import (
    MACRO_TIMEOUT_PAGAMENTO_SEG,
    MACRO_DELAY_ORDER_PIX_EMAIL_SEG,
    MACRO_CUPOM_PEDIDO_1_HORAS,
    MACRO_CUPOM_PEDIDO_2_HORAS,
    MACRO_CUPOM_PEDIDO_3_HORAS,
    MACRO_PERDIDO_PEDIDO_HORAS,
    MACRO_PRECHECK_MAX_DAYS
)
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol
from src.domain.events import OrderTransitionEvent
from src.services.notification_service import NotificationService
from src.core.time_utils import get_now_utc, parse_yampi_date_to_utc

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
        self.notification_service = NotificationService(message_provider, config)
        
    def process(self) -> None:
        logger.info("Iniciando processamento de pedidos (STG)...")
        
        try:
            import sentry_sdk
            tx_ctx = sentry_sdk.start_transaction(op="worker.process", name="OrderProcessor.process")
        except Exception:
            from contextlib import nullcontext
            tx_ctx = nullcontext()

        with tx_ctx:
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
                        o_id = order.get('id', 'N/A')
                        o_num = order.get('number', 'N/A')
                        logger.info(f">>> Processando Pedido {idx}/{len(eligible_orders)} | ID: # {o_id} (Nº {o_num})")
                        self._process_order_concurrently(order)
                else:
                    logger.info(f"Iniciando processamento assíncrono para {len(eligible_orders)} pedidos com até {self.config.MAX_WORKERS} workers...")
                    with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                        # O list() força a iteração, garantindo que qualquer exceção que fuja do worker vaze para a main thread
                        list(executor.map(self._process_order_concurrently, eligible_orders))
                    
                logger.info("Processamento finalizado.")
            except Exception as e:
                logger.error(f"Erro no processamento concorrente de pedidos: {e}")

    def _precheck_order(self, order: Dict[str, Any]) -> Tuple[bool, bool]:
        order_id = str(order.get('id', 'N/A'))
        order_number = str(order.get('number', 'N/A'))
        created_at_str = order.get('created_at', {}).get('date')
        
        logger.debug(f"[PRECHECK] Avaliando Pedido ID: # {order_id} (Nº {order_number})...")
        
        if not created_at_str:
            logger.debug(f"[PRECHECK] Pedido ID: # {order_id} (Nº {order_number}): Sem data de criação (created_at). Decisão: continuar busca, desqualificar pedido (should_continue=True, is_eligible=False).")
            return True, False
            
        try:
            created_at = parse_yampi_date_to_utc(order.get("created_at"))
        except ValueError as e:
            logger.error(f"Erro crítico de fuso horário no created_at do pedido {order_id}: {e}")
            return True, False
            
        now_utc = get_now_utc()
        days_since_creation = (now_utc - created_at).total_seconds() / (3600 * 24)
        
        logger.debug(
            f"[PRECHECK] Pedido ID: # {order_id} (Nº {order_number}) | Data do Pedido: {created_at_str} | Hora Atual (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Idade: {days_since_creation:.2f} dias"
        )
        
        if days_since_creation > MACRO_PRECHECK_MAX_DAYS:
            logger.debug(f"[PRECHECK] Pedido ID: # {order_id} (Nº {order_number}): Idade > {MACRO_PRECHECK_MAX_DAYS} dias ({days_since_creation:.2f}d). Regra atingida: Parar busca de novos pedidos (should_continue=False, is_eligible=False).")
            return False, False
            
        logger.debug(f"[PRECHECK] Pedido ID: # {order_id} (Nº {order_number}): Idade <= {MACRO_PRECHECK_MAX_DAYS} dias ({days_since_creation:.2f}d). Decisão: Qualificado para processamento (should_continue=True, is_eligible=True).")
        return True, True


    def _get_cart_id(self, order: Dict[str, Any]) -> Optional[str]:
        metadata = order.get('metadata', {}).get('data', [])
        for meta in metadata:
            if meta.get('key') == 'cart_id':
                return meta.get('value')
        return None

    def _get_tracking_code(self, order: Dict[str, Any]) -> Optional[str]:
        shipments = order.get('shipments', {}).get('data', [])
        shipment_data = shipments[0] if isinstance(shipments, list) and len(shipments) > 0 else {}
        found_code = (
            order.get('track_code') or 
            order.get('tracking_code') or 
            shipment_data.get('track_code') or 
            shipment_data.get('tracking_code')
        )
        if found_code and str(found_code).strip():
            return str(found_code).strip()
        return None

    def _process_order_concurrently(self, order: Dict[str, Any]) -> None:
        try:
            self._process_order_logic(order)
        except Exception as e:
            order_id = str(order.get('id', 'N/A'))
            order_number = str(order.get('number', 'N/A'))
            logger.error(f"[Worker Pedidos] Erro fatal e não tratado ao processar pedido ID: # {order_id} (Nº {order_number}): {e}", exc_info=True)

    def _extract_customer_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        cust = order.get('customer')
        if isinstance(cust, dict):
            if 'data' in cust and isinstance(cust['data'], dict):
                return cust['data']
            return cust
        return {}

    def _process_order_logic(self, order: Dict[str, Any]) -> None:
        order_id = str(order.get('id', ''))
        order_number = str(order.get('number', 'N/A'))
        cart_id = self._get_cart_id(order)
        if not cart_id:
            logger.warning(f"[Worker Pedidos] Pedido ID: # {order_id} (Nº {order_number}) ignorado pois não possui cart_id no metadata.")
            return

        data_pedido_payload = None
        transactions = order.get("transactions", {}).get("data", [])
        if transactions and transactions[0].get("created_at"):
            data_pedido_payload = transactions[0].get("created_at")
        else:
            data_pedido_payload = order.get("updated_at")

        try:
            data_pedido = parse_yampi_date_to_utc(data_pedido_payload)
        except ValueError as e:
            logger.error(f"Erro crítico de fuso horário na data base do pedido {order_id}: {e}")
            return

        customer_data = self._extract_customer_data(order)
        cpf = customer_data.get('cpf')
        raw_name = customer_data.get('name', 'Cliente') or 'Cliente'
        name = raw_name.strip().split()[0] if raw_name.strip() else 'Cliente'
        raw_email = customer_data.get('email')
        email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

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
        # FASE 1: LEITURA E VINCULAÇÃO ATÔMICA
        row = self.state_repo.upsert_from_order(cart_id, order_id, order_number, data_pedido, cpf, sku)
        if not row:
            logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}): Falha ao realizar upsert no repositório de estado.")
            return
            
        stg = row.get('stg')
        logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) (cart_id={cart_id}): Estado atual lido no banco STG={stg}")

        # FASE 2: PROCESSAMENTO E I/O EXTERNO
        if stg in (3, 8, 95, 96, 97):
            logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) (cart_id={cart_id}): Estado STG={stg} é um estado terminal. Nenhum processamento necessário.")
            return
            
        status_id = order.get('status', {}).get('data', {}).get('id')
        alias = str(order.get('status', {}).get('data', {}).get('alias', '')).lower()
        
        # Mapeamento dos status da Yampi (on_carriage restrito explicitamente)
        is_on_carriage = alias == 'on_carriage'
        is_paid = is_on_carriage or status_id in (4, 5, 6, 7, 9) or alias in ('paid', 'in_separation', 'invoiced', 'ready_for_shipping', 'shipped', 'delivered')
        is_pending = status_id in (1, 2, 3) or alias in ('created', 'authorized', 'waiting_payment')
        is_cancelled = status_id in (8, 12) or alias in ('cancelled', 'refunded')
        
        now_utc = get_now_utc()
        diff_hours = (now_utc - data_pedido).total_seconds() / 3600
        diff_seconds = (now_utc - data_pedido).total_seconds()

        logger.debug(
            f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) | Status Yampi: id={status_id}, alias='{alias}' "
            f"(is_paid={is_paid}, is_on_carriage={is_on_carriage}, is_pending={is_pending}, is_cancelled={is_cancelled}) | "
            f"Hora Pedido: {data_pedido} | Hora Atual (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Diff: {diff_seconds:.0f}s ({diff_hours:.2f}h)"
        )

        is_refunded = alias == 'refunded'
        
        new_stg = None
        template_name = None
        subject = ""

        # REGRA PRIORITÁRIA 1: Reembolsado na Yampi -> STG 8 (Terminal)
        if is_refunded:
            new_stg = 8
            logger.debug(f"[REGRA APLICADA] STG {stg} -> 8: Pedido ID: # {order_id} (Nº {order_number}) foi reembolsado na Yampi (alias='{alias}').")
        
        # REGRA PRIORITÁRIA 2: Em Transporte / En enviado (on_carriage / shipped) -> STG 3 + envio_rastreio
        elif is_on_carriage:
            if stg != 3:
                tracking_code = self._get_tracking_code(order)
                if tracking_code:
                    new_stg = 3
                    template_name = "pedido_a_caminho"
                    subject = f"Seu pedido #{order_number} está a caminho!"
                    logger.debug(f"[REGRA APLICADA] STG {stg} -> 3: Pedido ID: # {order_id} (Nº {order_number}) em transporte (alias='{alias}') com código '{tracking_code}'. Disparando e-mail com código de rastreio.")
                else:
                    logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) em transporte (alias='{alias}'), mas código de rastreio ainda ausente na Yampi. Transição para STG 3 bloqueada. Permanece STG={stg}.")
                
        # REGRA 3: Demais status pagos (paid, in_separation, invoiced)
        elif is_paid:
            if stg is None:
                new_stg = 1
                template_name = "pedido_aprovado"
                subject = f"Pagamento Confirmado: Pedido # {order_number}"
                logger.debug(f"[REGRA APLICADA] STG None -> 1: Pedido ID: # {order_id} (Nº {order_number}) com pagamento aprovado (alias='{alias}').")
            elif stg in (2, 4, 5, 6, 7):
                tracking_code = self._get_tracking_code(order)
                if tracking_code:
                    new_stg = 3
                    template_name = "pedido_aprovado"
                    subject = f"Pagamento Confirmado: Pedido # {order_number}"
                    logger.debug(f"[REGRA APLICADA] STG {stg} -> 3: Pedido ID: # {order_id} (Nº {order_number}) mudou para pago (alias='{alias}') com código '{tracking_code}'. Encerra esteira de cobrança.")
                else:
                    logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) mudou para pago (alias='{alias}'), mas código de rastreio ainda ausente na Yampi. Transição para STG 3 bloqueada. Permanece STG={stg}.")

        # REGRA 4: Status pendentes (waiting_payment, created, authorized) ou cancelados
        else:
            if stg is None:
                if diff_seconds <= MACRO_TIMEOUT_PAGAMENTO_SEG:
                    if is_pending:
                        if diff_seconds >= MACRO_DELAY_ORDER_PIX_EMAIL_SEG:
                            new_stg = 2
                            template_name = "pedido_pendente"
                            subject = f"Finalize seu pagamento: Pedido # {order_number}"
                            logger.debug(f"[REGRA APLICADA] STG None -> 2: Pedido ID: # {order_id} (Nº {order_number}) pendente com delay cumprido ({diff_seconds:.0f}s >= {MACRO_DELAY_ORDER_PIX_EMAIL_SEG}s).")
                        else:
                            logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) pendente aguardando delay de segurança ({diff_seconds:.0f}s < {MACRO_DELAY_ORDER_PIX_EMAIL_SEG}s).")
                    elif is_cancelled:
                        logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) cancelado precocemente. Aguardando timeout de 30min para ir ao STG 4.")
                else:
                    new_stg = 4
                    logger.debug(f"[REGRA APLICADA] STG None -> 4: Pedido ID: # {order_id} (Nº {order_number}) ultrapassou timeout ({diff_seconds:.0f}s > {MACRO_TIMEOUT_PAGAMENTO_SEG}s) sem pagamento.")
            elif stg == 2:
                if diff_seconds > MACRO_TIMEOUT_PAGAMENTO_SEG:
                    new_stg = 4
                    logger.debug(f"[REGRA APLICADA] STG 2 -> 4: Pedido ID: # {order_id} (Nº {order_number}) expirou janela de pagamento ({diff_seconds:.0f}s > {MACRO_TIMEOUT_PAGAMENTO_SEG}s).")
            elif stg == 4:
                if diff_hours > MACRO_CUPOM_PEDIDO_1_HORAS:
                    new_stg = 5
                    template_name = "cupom_pedido_1"
                    subject = f"10% de desconto para o seu pedido # {order_number}"
                    logger.debug(f"[REGRA APLICADA] STG 4 -> 5: Pedido ID: # {order_id} (Nº {order_number}) atingiu tempo para Cupom 1 ({diff_hours:.2f}h > {MACRO_CUPOM_PEDIDO_1_HORAS}h).")
            elif stg == 5:
                if diff_hours > MACRO_CUPOM_PEDIDO_2_HORAS:
                    new_stg = 6
                    template_name = "cupom_pedido_2"
                    subject = f"15% de desconto para o seu pedido # {order_number}"
                    logger.debug(f"[REGRA APLICADA] STG 5 -> 6: Pedido ID: # {order_id} (Nº {order_number}) atingiu tempo para Cupom 2 ({diff_hours:.2f}h > {MACRO_CUPOM_PEDIDO_2_HORAS}h).")
            elif stg == 6:
                if diff_hours > MACRO_CUPOM_PEDIDO_3_HORAS:
                    new_stg = 7
                    template_name = "cupom_pedido_3"
                    subject = f"20% de desconto! Última chance pedido # {order_number}"
                    logger.debug(f"[REGRA APLICADA] STG 6 -> 7: Pedido ID: # {order_id} (Nº {order_number}) atingiu tempo para Cupom 3 ({diff_hours:.2f}h > {MACRO_CUPOM_PEDIDO_3_HORAS}h).")
            elif stg == 7:
                if diff_hours > MACRO_PERDIDO_PEDIDO_HORAS:
                    new_stg = 8
                    logger.debug(f"[REGRA APLICADA] STG 7 -> 8: Pedido ID: # {order_id} (Nº {order_number}) marcado como perdido ({diff_hours:.2f}h > {MACRO_PERDIDO_PEDIDO_HORAS}h).")

        if new_stg is not None:
            success = True
            if template_name and email:
                event = OrderTransitionEvent(
                    order_id=order_id,
                    order_number=order_number,
                    new_stg=new_stg,
                    customer_data=customer_data,
                    order_data=order
                )
                success = self.notification_service.handle_transition(event, template_name)

            # FASE 3: GRAVAÇÃO ATÔMICA
            if success:
                self.state_repo.update_stg(cart_id, new_stg)
                logger.info(f"[Worker Pedidos] Estado do cart_id {cart_id} atualizado para STG={new_stg}")
                try:
                    import sentry_sdk
                    sentry_sdk.add_breadcrumb(
                        category="order_state_machine",
                        message=f"Pedido {order_id} (cart_id={cart_id}) transitou para STG={new_stg}",
                        level="info",
                        data={"order_id": order_id, "cart_id": cart_id, "new_stg": new_stg, "previous_stg": stg}
                    )
                except Exception:
                    pass
            else:
                logger.warning(f"[Worker Pedidos] Falha no envio de notificação para pedido {order_id}. Transição STG abortada (será retentada na próxima iteração).")
        else:
            logger.debug(f"[DECISÃO STG] Pedido ID: # {order_id} (Nº {order_number}) (cart_id={cart_id}): Nenhuma transição aplicável nesta rodada. Permanece STG={stg}.")
