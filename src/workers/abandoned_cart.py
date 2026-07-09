import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from src.core.config import Config
from src.domain.interfaces import YampiClientProtocol, MessageProviderProtocol, StateRepositoryProtocol

logger = logging.getLogger(__name__)

class AbandonedCartProcessor:
    """
    Worker principal responsável por orquestrar a lógica do carrinho abandonado.
    Ele recebe as dependências via Injeção de Dependência, obedecendo aos contratos (Interfaces).
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
        logger.info("Iniciando processamento de carrinhos abandonados...")
        
        try:
            # Vamos listar usando os filtros padrão
            carts_generator = self.api_client.get_abandoned_carts(include=['customer'])
            
            processed_count = 0
            for cart in carts_generator:
                self._handle_cart(cart)
                processed_count += 1
                
            logger.info(f"Processamento finalizado. {processed_count} carrinhos analisados.")
        except Exception as e:
            logger.error(f"Erro ao processar carrinhos: {e}")
            
    def _handle_cart(self, cart: Dict[str, Any]) -> None:
        cart_id = str(cart.get('id', ''))
        
        # Extrair dados do cliente
        customer_data = cart.get('customer', {}).get('data', {})
        phone = customer_data.get('phone', {}).get('full_number')
        name = customer_data.get('name', 'Cliente')
        
        if not phone:
            logger.debug(f"Carrinho {cart_id} ignorado: Cliente sem telefone cadastrado.")
            return
            
        # Verificar o tempo do abandono.
        updated_at_str = cart.get('updated_at', {}).get('date')
        if not updated_at_str:
            return
            
        try:
            # Parse da string de data
            updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                 logger.debug(f"Erro ao fazer parse da data para o carrinho {cart_id}: {updated_at_str}")
                 return
                 
        # A Yampi API devolve datas em UTC ou timezone local. Vamos comparar em UTC/local dependendo do retorno.
        # Por segurança, fazemos a comparação de tempo relativo simples.
        now = datetime.now()
        hours_since_abandonment = (now - updated_at).total_seconds() / 3600
        
        # Regra 1: Mensagem WhatsApp de 2h
        if hours_since_abandonment >= self.config.MESSAGE_1_DELAY_HOURS:
            message_type = 'whatsapp_2h'
            
            # Verifica se já recebeu
            if not self.state_repo.has_received_message(cart_id, message_type):
                logger.info(f"Carrinho {cart_id} qualificado para Mensagem 1 (WhatsApp). Abandonado há {hours_since_abandonment:.2f}h.")
                
                # Montar a mensagem básica que temos dados possíveis agora
                message_text = f"Olá {name}, vimos que você deixou itens no carrinho. Finalize sua compra agora!"
                
                # Enviar
                success = self.message_provider.send_whatsapp_message(phone, message_text)
                
                # Registrar no estado se sucesso
                if success:
                    self.state_repo.mark_message_sent(cart_id, message_type, datetime.utcnow())
                    logger.info(f"Mensagem {message_type} registrada no banco para o carrinho {cart_id}")
            else:
                logger.debug(f"Carrinho {cart_id} já recebeu a mensagem {message_type}.")
        else:
            logger.debug(f"Carrinho {cart_id} não atingiu o tempo mínimo para a primeira mensagem (abandonado há {hours_since_abandonment:.2f}h).")
