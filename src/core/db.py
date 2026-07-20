import sqlite3
import logging
from datetime import datetime
from src.domain.interfaces import StateRepositoryProtocol
from src.core.config import Config

logger = logging.getLogger(__name__)

class SQLiteStateRepository(StateRepositoryProtocol):
    """
    Implementação do StateRepositoryProtocol usando SQLite local.
    Responsável por persistir o estado das mensagens enviadas.
    """
    def __init__(self, config: Config):
        self.db_path = config.SQLITE_DB_PATH
        self._init_db()
        
    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages_sent (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cart_id TEXT NOT NULL,
                        message_type TEXT NOT NULL,
                        sent_at TIMESTAMP NOT NULL,
                        UNIQUE(cart_id, message_type)
                    )
                ''')
                conn.commit()
                logger.info(f"Banco de dados SQLite inicializado em {self.db_path}")
        except Exception as e:
            logger.error(f"Erro ao inicializar o banco de dados: {e}")
            raise

    def mark_message_sent(self, cart_id: str, message_type: str, sent_at: datetime) -> None:
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO messages_sent (cart_id, message_type, sent_at) VALUES (?, ?, ?)',
                    (cart_id, message_type, sent_at)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar estado da mensagem no DB: {e}")

    def has_received_message(self, cart_id: str, message_type: str) -> bool:
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT 1 FROM messages_sent WHERE cart_id = ? AND message_type = ?',
                    (cart_id, message_type)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Erro ao ler do DB: {e}")
            return False
