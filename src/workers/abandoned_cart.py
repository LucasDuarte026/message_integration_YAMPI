import logging
import os
import concurrent.futures
from datetime import datetime
from typing import Any, Dict, Tuple

from src.core.config import Config
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol

logger = logging.getLogger(__name__)

class AbandonedCartProcessor:
    """
    Worker principal responsável por orquestrar a lógica do carrinho abandonado.
    Ele consome os dados da API Yampi e dispara notificações de recuperação por E-mail concorrentemente.
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
        logger.info("Iniciando processamento de carrinhos abandonados (3 fases)...")
        
        try:
            carts_generator = self.api_client.get_abandoned_carts(include=['customer', 'items'])
            
            eligible_carts = []
            for cart in carts_generator:
                should_continue, is_eligible, phase, hours_since_abandonment = self._precheck_cart(cart)
                if is_eligible:
                    eligible_carts.append((cart, phase, hours_since_abandonment))
                if not should_continue:
                    break
            
            if not eligible_carts:
                logger.info("Nenhum carrinho qualificado para processamento nesta rodada.")
                return
                
            logger.info(f"Iniciando processamento assíncrono para {len(eligible_carts)} carrinhos com até {self.config.MAX_WORKERS} workers...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                # We pass the tuple (cart, phase, hours) directly
                executor.map(self._process_cart_concurrently, eligible_carts)
                
            logger.info("Processamento assíncrono finalizado.")
        except Exception as e:
            logger.error(f"Erro no processamento concorrente de carrinhos: {e}")
            
    def _precheck_cart(self, cart: Dict[str, Any]) -> Tuple[bool, bool, str, float]:
        """
        Retorna (should_continue_fetching, is_eligible, phase, hours_since_abandonment).
        Fases: 'lembrete' (4h), 'cupom_1' (24h), 'cupom_2' (48h).
        """
        cart_id = str(cart.get('id', ''))
        customer_data = cart.get('customer', {}).get('data', {})
        email = customer_data.get('email')
        
        if not email:
            return True, False, "", 0.0
            
        updated_at_str = cart.get('updated_at', {}).get('date')
        if not updated_at_str:
            return True, False, "", 0.0
            
        try:
            updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                 return True, False, "", 0.0
                 
        now = datetime.utcnow()
        hours_since_abandonment = (now - updated_at).total_seconds() / 3600
        
        # Determina a fase
        phase = ""
        if hours_since_abandonment >= 48:
            phase = "cupom_2"
        elif hours_since_abandonment >= 24:
            phase = "cupom_1"
        elif hours_since_abandonment >= 4: # 4 horas
            phase = "lembrete"
            
        logger.info(f"Analisando carrinho {cart_id}: abandonado há {hours_since_abandonment:.2f} horas. Regra aplicada: {phase or 'nenhuma'}.")
        
        if self.state_repo.is_cart_abandoned_72h(cart_id):
            return True, False, "", hours_since_abandonment
            
        if hours_since_abandonment >= 72:
            logger.info(f"Carrinho {cart_id} passou de 72h. Marcando como abandonado permanentemente.")
            self.state_repo.mark_cart_abandoned_72h(cart_id)
            # Para não buscar a vida toda, um limite hard de 1 semana
            if hours_since_abandonment > 168:
                return False, False, "", hours_since_abandonment
            return True, False, "", hours_since_abandonment
            
        if phase:
            if not self.state_repo.has_cart_received_email(cart_id, phase):
                return True, True, phase, hours_since_abandonment
                
        return True, False, "", hours_since_abandonment
        
    def _read_template(self, phase: str) -> str:
        template_path = os.path.join("src", "templates", "emails", f"{phase}.html")
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao ler template {template_path}: {e}")
            return ""

    def _process_cart_concurrently(self, cart_data: Tuple[Dict[str, Any], str, float]) -> None:
        cart, phase, hours_since_abandonment = cart_data
        cart_id = str(cart.get('id', ''))
        customer_data = cart.get('customer', {}).get('data', {})
        name = customer_data.get('name', 'Cliente').split()[0]
        
        items_html = ""
        total_value = 0.0
        
        items_raw = cart.get("items", {})
        if isinstance(items_raw, dict) and "data" in items_raw:
            items_list = items_raw["data"]
        elif isinstance(items_raw, list):
            items_list = items_raw
        else:
            items_list = []
            
        for item in items_list:
            title = item.get("title") or item.get("product_title") or "Produto"
            price_raw = item.get("price") or item.get("product_price") or 0.0
            try:
                price = float(price_raw)
            except (ValueError, TypeError):
                price = 0.0
                
            qty = int(item.get("quantity", 1))
            subtotal = price * qty
            total_value += subtotal
            
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

        recovery_url = cart.get("recovery_url") or cart.get("checkout_url") or "https://yampi.com.br"
        
        html_body = self._read_template(phase)
        if not html_body:
            return
            
        html_body = html_body.replace("{name}", name)
        html_body = html_body.replace("{items_html}", items_html)
        html_body = html_body.replace("{total_value:.2f}", f"{total_value:.2f}")
        html_body = html_body.replace("{recovery_url}", recovery_url)
        
        folder_path = os.path.join("emails", f"cart_{cart_id}")
        file_path = os.path.join(folder_path, f"email_{phase}.html")
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_body)
            logger.info(f"[Worker] HTML da fase '{phase}' para carrinho {cart_id} (abandonado há {hours_since_abandonment:.2f} horas) salvo em: {file_path}")
        except Exception as e:
            logger.error(f"[Worker] Falha ao criar HTML para o carrinho {cart_id}: {e}")

        # Sempre enviar para o email de teste conforme config (ou fallback pro real em prod)
        recipient_email = self.config.TEST_EMAIL_RECIPIENT
        
        subjects = {
            "lembrete": f"{name}, seu carrinho está te esperando!",
            "cupom_1": f"{name}, ganhe 10% OFF nos seus itens!",
            "cupom_2": f"Última chance, {name}! 20% OFF no seu carrinho"
        }
        subject = subjects.get(phase, "Seu carrinho abandonado")
        
        success = self.message_provider.send_email_message(recipient_email, subject, html_body)
        
        if success:
            self.state_repo.mark_cart_email_sent(cart_id, phase, datetime.utcnow())
            logger.info(f"[Worker] E-mail '{phase}' registrado para o carrinho {cart_id} (abandonado há {hours_since_abandonment:.2f} horas)")
