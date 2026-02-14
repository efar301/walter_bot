import sqlite3

from ..config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS topics (
        topic_id INTEGER PRIMARY KEY,
        exam TEXT NOT NULL,
        name TEXT NOT NULL,
        CONSTRAINT exam_topic UNIQUE (exam, name)
    )
    """
)

conn.commit()
conn.close()
