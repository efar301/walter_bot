import sqlite3

from walter.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS question_topics (
        exam TEXT NOT NULL,
        question_number INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        FOREIGN KEY (topic_id) REFERENCES topics(topic_id),
        PRIMARY KEY (exam, question_number, topic_id)
    )
    """
)

conn.commit()
conn.close()
