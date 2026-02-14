import sqlite3

from walter.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        stat_decay INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """
)

conn.commit()
conn.close()
