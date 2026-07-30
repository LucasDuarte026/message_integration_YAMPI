from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class OrderTransitionEvent:
    order_id: str
    order_number: str
    new_stg: int
    customer_data: Dict[str, Any]
    order_data: Dict[str, Any]

@dataclass
class CartTransitionEvent:
    cart_id: str
    new_stc: int
    customer_data: Dict[str, Any]
    cart_data: Dict[str, Any]
