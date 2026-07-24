import logging
import os
import concurrent.futures
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from src.core.config import Config
from src.core.macros import (
    MACRO_CUPOM_CARRINHO_1_HORAS,
    MACRO_CUPOM_CARRINHO_2_HORAS,
    MACRO_CUPOM_CARRINHO_3_HORAS,
    MACRO_PERDIDO_CARRINHO_HORAS
)
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol

logger = logging.getLogger(__name__)

class AbandonedCartProcessor:
    """
    Worker principal responsável por orquestrar a lógica do carrinho abandonado (STC).
    Ele consome os dados da API Yampi e dispara notificações de recuperação concorrentemente.
    """
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
        logger.info("Iniciando processamento de carrinhos abandonados (STC)...")
        
        try:
            carts_generator = self.api_client.get_abandoned_carts(include=['customer', 'items'])
            
            eligible_carts = []
            for cart in carts_generator:
                should_continue, is_eligible = self._precheck_cart(cart)
                if is_eligible:
                    eligible_carts.append(cart)
                if not should_continue:
                    break
            
            if not eligible_carts:
                logger.info("Nenhum carrinho qualificado para processamento nesta rodada.")
                return
                
            if self.config.MAX_WORKERS <= 1: # util no modo debug
                logger.info(f"Modo de DEBUG Síncrono (MAX_WORKERS={self.config.MAX_WORKERS}): Processando {len(eligible_carts)} carrinhos um a um...")
                for idx, cart in enumerate(eligible_carts, 1):
                    logger.info(f">>> Processando Carrinho {idx}/{len(eligible_carts)}")
                    self._process_cart_concurrently(cart)
            else:
                logger.info(f"Iniciando processamento assíncrono para {len(eligible_carts)} carrinhos com até {self.config.MAX_WORKERS} workers...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                    executor.map(self._process_cart_concurrently, eligible_carts)
                    
            logger.info("Processamento finalizado.")
        except Exception as e:
            logger.error(f"Erro no processamento concorrente de carrinhos: {e}")
            
    def _precheck_cart(self, cart: Dict[str, Any]) -> Tuple[bool, bool]:
        created_at_str = cart.get('created_at', {}).get('date')
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
        hours_since_abandonment = (now_utc3 - created_at).total_seconds() / 3600
        
        # Limite de busca: Não olhar mais longe que 168 horas (1 semana)
        if hours_since_abandonment > 168:
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

    def _process_cart_concurrently(self, cart: Dict[str, Any]) -> None:
        cart_id = str(cart.get('id', ''))
        customer_data = cart.get('customer', {}).get('data', {})
        cpf = customer_data.get('cpf')
        name = customer_data.get('name', 'Cliente').split()[0]
        email = customer_data.get('email')
        
        if not email:
            logger.warning(f"[Worker Carrinhos] Carrinho {cart_id} sem email. Ignorando.")
            return

        created_at_str = cart.get('created_at', {}).get('date')
        try:
            data_carrinho = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            data_carrinho = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S.%f")

        # Determinar SKU mais caro e calcular total
        sku = None
        highest_price = -1
        total_value = 0.0
        items_html = ""
        
        items_raw = cart.get("items", {})
        items_list = items_raw.get("data", []) if isinstance(items_raw, dict) else (items_raw if isinstance(items_raw, list) else [])
            
        for item in items_list:
            item_sku = item.get("item_sku") or item.get("sku", {}).get("data", {}).get("sku")
            title = item.get("title") or item.get("product_title") or "Produto"
            price_raw = item.get("price") or item.get("product_price") or 0.0
            try:
                price = float(price_raw)
            except (ValueError, TypeError):
                price = 0.0
                
            if price > highest_price and item_sku:
                highest_price = price
                sku = item_sku
                
            qty = int(item.get("quantity", 1))
            subtotal = price * qty
            total_value += subtotal
            
            items_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155;"><strong>{title}</strong></td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: center;">{qty}</td>
                <td style="padding: 12px; font-family: sans-serif; font-size: 14px; color: #334155; text-align: right;">R$ {price:.2f}</td>
            </tr>
            """

        recovery_url = cart.get("simulate_url") or cart.get("recovery_url") or cart.get("checkout_url") or "https://yampi.com.br"

        # FASE 1: LEITURA ATÔMICA
        row = self.state_repo.upsert_from_cart(cart_id, data_carrinho, cpf, sku)
        if not row:
            return
            
        order_id = row.get('order_id')
        if order_id is not None:
            # Carrinho já virou pedido, worker de carrinhos não deve mais tocar
            logger.info(f"[Worker Carrinhos] Carrinho {cart_id} ignorado, pois já converteu no pedido {order_id}.")
            return

        stc = row.get('stc')

        # FASE 2: PROCESSAMENTO E I/O EXTERNO
        if stc in (18, 85, 86, 87):
            return  # ESTADO TERMINAL, pula
            
        now_utc3 = datetime.utcnow() - timedelta(hours=3)
        diff_hours = (now_utc3 - data_carrinho).total_seconds() / 3600
        
        new_stc = None
        template_name = None
        subject = ""

        if stc is None:
            if diff_hours > MACRO_CUPOM_CARRINHO_1_HORAS:
                new_stc = 15
                template_name = "cupom_4_carrinho"
                subject = f"{name}, seu carrinho está te esperando!"
        elif stc == 15:
            if diff_hours > MACRO_CUPOM_CARRINHO_2_HORAS:
                new_stc = 16
                template_name = "cupom_5_carrinho"
                subject = f"{name}, ganhe um desconto especial nos seus itens!"
        elif stc == 16:
            if diff_hours > MACRO_CUPOM_CARRINHO_3_HORAS:
                new_stc = 17
                template_name = "cupom_6_carrinho"
                subject = f"Última chance, {name}! Mega desconto no seu carrinho"
        elif stc == 17:
            if diff_hours > MACRO_PERDIDO_CARRINHO_HORAS:
                new_stc = 18

        if new_stc is not None:
            if template_name:
                html_body = self._read_template(template_name)
                if html_body:
                    html_body = html_body.replace("{name}", name)
                    html_body = html_body.replace("{items_html}", items_html)
                    html_body = html_body.replace("{total_value}", f"{total_value:.2f}")
                    html_body = html_body.replace("{total_value:.2f}", f"{total_value:.2f}")
                    html_body = html_body.replace("{recovery_url}", recovery_url)
                    
                    folder_path = os.path.join("emails", f"cart_{cart_id}")
                    file_path = os.path.join(folder_path, f"email_stc_{new_stc}.html")
                    try:
                        os.makedirs(folder_path, exist_ok=True)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(html_body)
                    except Exception as e:
                        logger.error(f"[Worker Carrinhos] Falha ao criar HTML para o carrinho {cart_id}: {e}")

                    recipient_email = self.config.TEST_EMAIL_RECIPIENT
                    self.message_provider.send_email_message(recipient_email, subject, html_body)
                    logger.info(f"[Worker Carrinhos] E-mail STC {new_stc} enviado para carrinho {cart_id}")

            # FASE 3: GRAVAÇÃO ATÔMICA
            self.state_repo.update_stc(cart_id, new_stc)
            logger.info(f"[Worker Carrinhos] Estado do cart_id {cart_id} atualizado para STC={new_stc}")
