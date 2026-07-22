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
    Define o contrato para Mock ou SMTP.
    """
        
    @abstractmethod
    def send_email_message(self, email: str, subject: str, html_body: str) -> bool:
        """
        Envia um e-mail.
        """
        pass

class StateRepositoryProtocol(Protocol):
    """
    Protocolo para o repositório que guardará os metadados de estado (PostgreSQL).
    Baseado no padrão de travamento e atualização em 3 fases para evitar deadlocks com SMTP lento.
    """
    
    def upsert_from_order(self, cart_id: str, pedido_id: str, data_pedido: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Fase 1 (Pedidos): Insere novo ou atualiza existente atrelando o pedido ao cart_id. Retorna a linha completa com lock temporário.
        """
        ...
        
    def upsert_from_cart(self, cart_id: str, data_carrinho: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Fase 1 (Carrinhos): Insere novo ou atualiza carrinho. Retorna a linha completa com lock temporário.
        """
        ...
        
    def update_stg(self, cart_id: str, new_stg: int) -> None:
        """
        Fase 3 (Pedidos): Grava o novo status (STG) e atualiza timestamp_ultimo_email.
        """
        ...
        
    def update_stc(self, cart_id: str, new_stc: int) -> None:
        """
        Fase 3 (Carrinhos): Grava o novo status (STC) e atualiza timestamp_ultimo_email.
        """
        ...
