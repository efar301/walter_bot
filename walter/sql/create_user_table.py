import sqlite3

from ..config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        created_at TEXT NOT NULL
    )
    """
)

conn.commit()
conn.close()
