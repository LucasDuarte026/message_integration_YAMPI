import logging
import os
import concurrent.futures
from datetime import datetime
from typing import Any, Dict, Tuple

from src.core.config import Config
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
        logger.info("Iniciando processamento de pedidos (2 fases: Pagamento e Rastreio)...")
        
        try:
            # We rely on the Yampi generator and just break if we go too far back in time
            orders_generator = self.api_client.get_orders(include=['customer', 'items', 'shipments', 'status'])
            
            eligible_orders = []
            for order in orders_generator:
                should_continue, is_eligible, phase = self._precheck_order(order)
                if is_eligible:
                    eligible_orders.append((order, phase))
                if not should_continue:
                    break
            
            if not eligible_orders:
                logger.info("Nenhum pedido qualificado para processamento nesta rodada.")
                return
                
            logger.info(f"Iniciando processamento assíncrono para {len(eligible_orders)} pedidos com até {self.config.MAX_WORKERS} workers...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                executor.map(self._process_order_concurrently, eligible_orders)
                
            logger.info("Processamento assíncrono finalizado.")
        except Exception as e:
            logger.error(f"Erro no processamento concorrente de pedidos: {e}")

    def _precheck_order(self, order: Dict[str, Any]) -> Tuple[bool, bool, str]:
        order_id = str(order.get('id', ''))
        
        created_at_str = order.get('created_at', {}).get('date')
        if not created_at_str:
            return True, False, ""
            
        try:
            # Ex: "2024-06-01 12:00:00"
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return True, False, ""
            
        # Cutoff: Don't process orders older than 14 days
        now = datetime.utcnow()
        days_since_creation = (now - created_at).total_seconds() / (3600 * 24)
        if days_since_creation > 14:
            return False, False, ""
            
        status = order.get('status', {}).get('data', {}).get('alias', '')
        status_id = order.get('status_id')
        
        # Phase: envio_rastreio
        # Check if we have tracking code
        shipments = order.get('shipments', {}).get('data', [])
        tracking_code = None
        for shipment in shipments:
            code = shipment.get('tracking_code')
            if code:
                tracking_code = code
                break
                
        # Some Yampi setups use status 'shipped' (alias) or status_id for shipped
        is_shipped = tracking_code is not None or status in ['shipped', 'em_transporte']
        is_paid = status in ['paid', 'pago'] or status_id == 3
        
        if is_shipped and tracking_code:
            if not self.state_repo.has_order_received_email(order_id, 'envio_rastreio'):
                return True, True, 'envio_rastreio'
        elif is_paid:
            if not self.state_repo.has_order_received_email(order_id, 'pagamento_efetuado'):
                return True, True, 'pagamento_efetuado'
                
        return True, False, ""

    def _read_template(self, phase: str) -> str:
        template_path = os.path.join("src", "templates", "emails", f"{phase}.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao ler template {template_path}: {e}")
            return ""

    def _process_order_concurrently(self, order_data: Tuple[Dict[str, Any], str]) -> None:
        order, phase = order_data
        order_id = str(order.get('id', ''))
        customer_data = order.get('customer', {}).get('data', {})
        name = customer_data.get('name', 'Cliente').split()[0]
        
        items_html = ""
        items_raw = order.get("items", {})
        if isinstance(items_raw, dict) and "data" in items_raw:
            items_list = items_raw["data"]
        elif isinstance(items_raw, list):
            items_list = items_raw
        else:
            items_list = []
            
        for item in items_list:
            title = item.get("name") or item.get("title") or "Produto"
            price = float(item.get("price", 0.0))
            qty = int(item.get("quantity", 1))
            items_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155;">
                    <strong>{title}</strong>
                </td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: center;">
                    {qty}
                </td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: right;">
                    R$ {price:.2f}
                </td>
            </tr>
            """

        tracking_code = ""
        tracking_url = "https://rastreamento.correios.com.br"
        if phase == 'envio_rastreio':
            shipments = order.get('shipments', {}).get('data', [])
            for shipment in shipments:
                if shipment.get('tracking_code'):
                    tracking_code = shipment.get('tracking_code')
                    tracking_url = shipment.get('tracking_url') or tracking_url
                    break
        
        html_body = self._read_template(phase)
        if not html_body:
            return
            
        html_body = html_body.replace("{name}", name)
        html_body = html_body.replace("{order_id}", order_id)
        html_body = html_body.replace("{items_html}", items_html)
        html_body = html_body.replace("{tracking_code}", tracking_code)
        html_body = html_body.replace("{tracking_url}", tracking_url)
        
        folder_path = os.path.join("emails", f"order_{order_id}")
        file_path = os.path.join(folder_path, f"email_{phase}.html")
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_body)
            logger.info(f"[Worker] HTML da fase '{phase}' para pedido {order_id} salvo em: {file_path}")
        except Exception as e:
            logger.error(f"[Worker] Falha ao criar HTML para o pedido {order_id}: {e}")

        recipient_email = self.config.TEST_EMAIL_RECIPIENT
        
        subjects = {
            "pagamento_efetuado": f"Pagamento Confirmado: Pedido #{order_id}",
            "envio_rastreio": f"O seu pedido #{order_id} está a caminho!"
        }
        subject = subjects.get(phase, f"Atualização do seu Pedido #{order_id}")
        
        success = self.message_provider.send_email_message(recipient_email, subject, html_body)
        
        if success:
            self.state_repo.mark_order_email_sent(order_id, phase, datetime.utcnow())
            logger.info(f"[Worker] E-mail '{phase}' registrado para o pedido {order_id}")
