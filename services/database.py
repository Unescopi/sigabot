import sqlite3

class Database:
    def __init__(self):
        self.db_file = "/app/data/status.db"
        self._create_tables()
    
    def _create_tables(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lado TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def atualizar_status(self, lado, status):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT INTO status_history (lado, status) VALUES (?, ?)",
                (lado, status)
            )