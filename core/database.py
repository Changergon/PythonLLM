#C:\PyProject\PythonLLM\core\database.py
import sqlite3
from datetime import datetime

class DialogueDB:
    def __init__(self, db_path="data/dialogues.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_message(self, model, role, content):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO dialogues (timestamp, model, role, content) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), model, role, content)
        )
        self.conn.commit()

    def get_dialog_history(self, model=None):
        cursor = self.conn.cursor()
        if model:
            cursor.execute("SELECT role, content FROM dialogues WHERE model = ? ORDER BY timestamp", (model,))
        else:
            cursor.execute("SELECT role, content FROM dialogues ORDER BY timestamp")
        return cursor.fetchall()

    def close(self):
        self.conn.close()