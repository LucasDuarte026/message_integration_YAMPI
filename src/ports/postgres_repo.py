import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
from src.domain.interfaces import StateRepositoryProtocol
from src.core.time_utils import get_now_utc
from contextlib import contextmanager, nullcontext
from psycopg2.pool import ThreadedConnectionPool
from src.core.macros import (
    MACRO_PG_POOL_MIN_CONN,
    MACRO_PG_POOL_MAX_CONN,
    MACRO_TIMEZONE_OFFSET_HOURS,
    MACRO_DEFAULT_FALLBACK_CPF,
    MACRO_DEFAULT_FALLBACK_SKU,
    MACRO_DEFAULT_FALLBACK_ORDER_NUMBER
)

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

logger = logging.getLogger(__name__)

class PostgresStateRepository(StateRepositoryProtocol):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = ThreadedConnectionPool(
            MACRO_PG_POOL_MIN_CONN, 
            MACRO_PG_POOL_MAX_CONN, 
            self.database_url, 
            cursor_factory=RealDictCursor
        )
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)

    def close(self):
        if hasattr(self, 'pool') and self.pool:
            self.pool.closeall()

    def _init_db(self):
        create_table = """
        CREATE TABLE IF NOT EXISTS email_status_table (
            cart_id VARCHAR(255) PRIMARY KEY,
            order_id VARCHAR(255) DEFAULT NULL,
            order_number VARCHAR(255) NOT NULL DEFAULT 'N/A',
            data_pedido TIMESTAMP DEFAULT NULL,
            data_carrinho TIMESTAMP DEFAULT NULL,
            cpf VARCHAR(14) NOT NULL,
            sku VARCHAR(255) NOT NULL,
            stg INTEGER DEFAULT NULL,
            stc INTEGER DEFAULT NULL,
            timestamp_ultimo_email TIMESTAMP DEFAULT NULL
        );
        """
        create_idx_cpf = "CREATE INDEX IF NOT EXISTS idx_email_status_cpf ON email_status_table (cpf);"
        create_idx_cpf_sku = "CREATE INDEX IF NOT EXISTS idx_email_status_cpf_sku ON email_status_table (cpf, sku);"
        create_idx_order_number = "CREATE INDEX IF NOT EXISTS idx_email_status_order_number ON email_status_table (order_number);"
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table)
                    cur.execute(create_idx_cpf)
                    cur.execute(create_idx_cpf_sku)
                    cur.execute(create_idx_order_number)
                conn.commit()
            logger.info("Banco de dados PostgreSQL inicializado com sucesso de acordo com a Especificação 04.")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados PostgreSQL: {e}")
            raise

    def upsert_from_order(self, cart_id: str, order_id: str, order_number: Optional[str], data_pedido: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        # Fallbacks de dados cadastrais para satisfazer NOT NULL da Spec 04
        safe_cpf = cpf if cpf else MACRO_DEFAULT_FALLBACK_CPF
        safe_sku = sku if sku else MACRO_DEFAULT_FALLBACK_SKU
        safe_order_number = str(order_number) if order_number else MACRO_DEFAULT_FALLBACK_ORDER_NUMBER

        # data_carrinho eh gravada como NULL quando criada pelo Pedido, a menos que o Worker de Carrinhos ja a tenha gravado
        query = """
            INSERT INTO email_status_table (cart_id, order_id, order_number, data_pedido, data_carrinho, cpf, sku)
            VALUES (%s, %s, %s, %s, NULL, %s, %s)
            ON CONFLICT (cart_id) DO UPDATE 
            SET order_id = EXCLUDED.order_id,
                order_number = EXCLUDED.order_number,
                data_pedido = EXCLUDED.data_pedido,
                cpf = EXCLUDED.cpf,
                sku = EXCLUDED.sku
            RETURNING *;
        """
        lock_query = "SELECT * FROM email_status_table WHERE cart_id = %s FOR UPDATE;"
        try:
            span_ctx = sentry_sdk.start_span(op="db.sql.query", name="Postgres upsert_from_order") if sentry_sdk else nullcontext()
        except Exception:
            span_ctx = nullcontext()

        try:
            with span_ctx:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (cart_id, order_id, safe_order_number, data_pedido, safe_cpf, safe_sku))
                        cur.execute(lock_query, (cart_id,))
                        result = cur.fetchone()
                    conn.commit()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Erro no upsert_from_order para cart_id {cart_id}: {e}")
            return None

    def upsert_from_cart(self, cart_id: str, data_carrinho: datetime, cpf: Optional[str], sku: Optional[str]) -> Optional[Dict[str, Any]]:
        safe_cpf = cpf if cpf else MACRO_DEFAULT_FALLBACK_CPF
        safe_sku = sku if sku else MACRO_DEFAULT_FALLBACK_SKU
        
        query = """
            INSERT INTO email_status_table (cart_id, order_number, data_carrinho, cpf, sku)
            VALUES (%s, 'N/A', %s, %s, %s)
            ON CONFLICT (cart_id) DO UPDATE 
            SET data_carrinho = COALESCE(LEAST(email_status_table.data_carrinho, EXCLUDED.data_carrinho), EXCLUDED.data_carrinho),
                cpf = EXCLUDED.cpf,
                sku = EXCLUDED.sku
            RETURNING *;
        """
        lock_query = "SELECT * FROM email_status_table WHERE cart_id = %s FOR UPDATE;"
        try:
            span_ctx = sentry_sdk.start_span(op="db.sql.query", name="Postgres upsert_from_cart") if sentry_sdk else nullcontext()
        except Exception:
            span_ctx = nullcontext()

        try:
            with span_ctx:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(query, (cart_id, data_carrinho, safe_cpf, safe_sku))
                        cur.execute(lock_query, (cart_id,))
                        result = cur.fetchone()
                    conn.commit()
                    return dict(result) if result else None
        except Exception as e:
            logger.error(f"Erro no upsert_from_cart para cart_id {cart_id}: {e}")
            return None

    def update_stg(self, cart_id: str, new_stg: int) -> None:
        query = """
            UPDATE email_status_table 
            SET stg = %s, timestamp_ultimo_email = %s 
            WHERE cart_id = %s;
        """
        try:
            span_ctx = sentry_sdk.start_span(op="db.sql.query", name="Postgres update_stg") if sentry_sdk else nullcontext()
        except Exception:
            span_ctx = nullcontext()

        try:
            with span_ctx:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        now_utc = get_now_utc()
                        cur.execute(query, (new_stg, now_utc, cart_id))
                    conn.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar STG do cart_id {cart_id} para {new_stg}: {e}")

    def update_stc(self, cart_id: str, new_stc: int) -> None:
        query = """
            UPDATE email_status_table 
            SET stc = %s, timestamp_ultimo_email = %s 
            WHERE cart_id = %s;
        """
        try:
            span_ctx = sentry_sdk.start_span(op="db.sql.query", name="Postgres update_stc") if sentry_sdk else nullcontext()
        except Exception:
            span_ctx = nullcontext()

        try:
            with span_ctx:
                with self._get_connection() as conn:
                    with conn.cursor() as cur:
                        now_utc = get_now_utc()
                        cur.execute(query, (new_stc, now_utc, cart_id))
                    conn.commit()
        except Exception as e:
            logger.error(f"Erro ao atualizar STC do cart_id {cart_id} para {new_stc}: {e}")

