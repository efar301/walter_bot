import sqlite3

from ..config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS attempts (
        user_id INTEGER NOT NULL,
        exam TEXT NOT NULL,
        question_number INTEGER NOT NULL,
        selected_answer TEXT NOT NULL,
        correct INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL,
        CONSTRAINT unique_attempt UNIQUE (user_id, exam, question_number),
        CONSTRAINT valid_selected_answer CHECK (selected_answer IN ('A', 'B', 'C', 'D', 'E')),
        CONSTRAINT valid_correct CHECK (correct IN (0, 1))
    )
    """
)

conn.commit()
conn.close()
