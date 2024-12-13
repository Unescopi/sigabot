import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = "/app/data/status.db"
        self._create_tables()
    
    def _create_tables(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lado TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def atualizar_status(self, lado, status):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO status_history (lado, status) VALUES (?, ?)",
                    (lado, status)
                )
                conn.commit()
                logger.info(f"Status atualizado: {lado}={status}")
                return True
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")
            return False
    
    def get_ultimo_status(self, lado):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status FROM status_history WHERE lado = ? ORDER BY timestamp DESC LIMIT 1",
                    (lado,)
                )
                result = cursor.fetchone()
                return result[0] if result else "LIBERADO"  # Status padrão
        except Exception as e:
            logger.error(f"Erro ao buscar status: {str(e)}")
            return "LIBERADO"  # Status padrão em caso de erro 