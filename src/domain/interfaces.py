from typing import Protocol, Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

class YampiClientProtocol(Protocol):
    """
    Contrato estrito (Spec) para comunicação com a API Yampi.
    Qualquer cliente (real ou mock) deve implementar esses métodos.
    """
    def get_orders(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Any:
        ...
        
    def get_abandoned_carts(self, filters: Optional[Dict[str, str]] = None, include: Optional[List[str]] = None) -> Any:
        ...

class MessageProviderProtocol(ABC):
    """
    Interface Abstrata (Spec) para disparadores de mensagens.
    Define o contrato para Twilio, Zenvia, ou Mocks.
    """
    
    @abstractmethod
    def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        """
        Envia uma mensagem de texto via WhatsApp.
        Deve retornar True se sucesso, False caso contrário.
        """
        pass
        
    @abstractmethod
    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        """
        (Futuro) Envia um e-mail.
        """
        pass

class StateRepositoryProtocol(Protocol):
    """
    Protocolo para o repositório que guardará os metadados de estado (PostgreSQL).
    """
    # Para Carrinhos Abandonados
    def mark_cart_email_sent(self, cart_id: str, email_type: str, sent_at: datetime) -> None:
        ...
        
    def has_cart_received_email(self, cart_id: str, email_type: str) -> bool:
        ...
        
    def mark_cart_abandoned_72h(self, cart_id: str) -> None:
        ...
        
    def is_cart_abandoned_72h(self, cart_id: str) -> bool:
        ...
        
    # Para Pedidos (Orders)
    def mark_order_email_sent(self, order_id: str, email_type: str, sent_at: datetime) -> None:
        ...
        
    def has_order_received_email(self, order_id: str, email_type: str) -> bool:
        ...
