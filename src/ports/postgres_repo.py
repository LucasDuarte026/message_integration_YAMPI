import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
from src.domain.interfaces import StateRepositoryProtocol

logger = logging.getLogger(__name__)

class PostgresStateRepository(StateRepositoryProtocol):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._init_db()

    def _get_connection(self):
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _init_db(self):
        create_carts_table = """
        CREATE TABLE IF NOT EXISTS cart_states (
            cart_id VARCHAR(255) PRIMARY KEY,
            email_lembrete_sent_at TIMESTAMP,
            email_cupom1_sent_at TIMESTAMP,
            email_cupom2_sent_at TIMESTAMP,
            is_abandoned_72h BOOLEAN DEFAULT FALSE
        );
        """
        create_orders_table = """
        CREATE TABLE IF NOT EXISTS order_states (
            order_id VARCHAR(255) PRIMARY KEY,
            email_pagamento_efetuado_sent_at TIMESTAMP,
            email_envio_rastreio_sent_at TIMESTAMP
        );
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_carts_table)
                    cur.execute(create_orders_table)
                conn.commit()
            logger.info("Banco de dados PostgreSQL inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados PostgreSQL: {e}")
            raise

    # Para Carrinhos Abandonados
    def mark_cart_email_sent(self, cart_id: str, email_type: str, sent_at: datetime) -> None:
        column_map = {
            'lembrete': 'email_lembrete_sent_at',
            'cupom_1': 'email_cupom1_sent_at',
            'cupom_2': 'email_cupom2_sent_at'
        }
        if email_type not in column_map:
            raise ValueError(f"Tipo de e-mail de carrinho inválido: {email_type}")
            
        column_name = column_map[email_type]
        query = f"""
            INSERT INTO cart_states (cart_id, {column_name}) 
            VALUES (%s, %s)
            ON CONFLICT (cart_id) DO UPDATE 
            SET {column_name} = EXCLUDED.{column_name};
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (cart_id, sent_at))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao marcar e-mail do carrinho {cart_id} como enviado: {e}")

    def has_cart_received_email(self, cart_id: str, email_type: str) -> bool:
        column_map = {
            'lembrete': 'email_lembrete_sent_at',
            'cupom_1': 'email_cupom1_sent_at',
            'cupom_2': 'email_cupom2_sent_at'
        }
        if email_type not in column_map:
            return False
            
        column_name = column_map[email_type]
        query = f"SELECT {column_name} FROM cart_states WHERE cart_id = %s;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (cart_id,))
                    result = cur.fetchone()
                    if result and result[column_name]:
                        return True
        except Exception as e:
            logger.error(f"Erro ao checar se carrinho {cart_id} recebeu e-mail: {e}")
        return False

    def mark_cart_abandoned_72h(self, cart_id: str) -> None:
        query = """
            INSERT INTO cart_states (cart_id, is_abandoned_72h) 
            VALUES (%s, TRUE)
            ON CONFLICT (cart_id) DO UPDATE 
            SET is_abandoned_72h = EXCLUDED.is_abandoned_72h;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (cart_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao marcar carrinho {cart_id} como abandonado > 72h: {e}")

    def is_cart_abandoned_72h(self, cart_id: str) -> bool:
        query = "SELECT is_abandoned_72h FROM cart_states WHERE cart_id = %s;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (cart_id,))
                    result = cur.fetchone()
                    if result and result['is_abandoned_72h']:
                        return True
        except Exception as e:
            logger.error(f"Erro ao checar status de abandono 72h do carrinho {cart_id}: {e}")
        return False

    # Para Pedidos (Orders)
    def mark_order_email_sent(self, order_id: str, email_type: str, sent_at: datetime) -> None:
        column_map = {
            'pagamento_efetuado': 'email_pagamento_efetuado_sent_at',
            'envio_rastreio': 'email_envio_rastreio_sent_at'
        }
        if email_type not in column_map:
            raise ValueError(f"Tipo de e-mail de pedido inválido: {email_type}")
            
        column_name = column_map[email_type]
        query = f"""
            INSERT INTO order_states (order_id, {column_name}) 
            VALUES (%s, %s)
            ON CONFLICT (order_id) DO UPDATE 
            SET {column_name} = EXCLUDED.{column_name};
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (order_id, sent_at))
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao marcar e-mail de pedido {order_id} como enviado: {e}")

    def has_order_received_email(self, order_id: str, email_type: str) -> bool:
        column_map = {
            'pagamento_efetuado': 'email_pagamento_efetuado_sent_at',
            'envio_rastreio': 'email_envio_rastreio_sent_at'
        }
        if email_type not in column_map:
            return False
            
        column_name = column_map[email_type]
        query = f"SELECT {column_name} FROM order_states WHERE order_id = %s;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (order_id,))
                    result = cur.fetchone()
                    if result and result[column_name]:
                        return True
        except Exception as e:
            logger.error(f"Erro ao checar se pedido {order_id} recebeu e-mail: {e}")
        return False
