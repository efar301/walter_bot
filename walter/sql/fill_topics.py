import csv
import sqlite3
from pathlib import Path

from walter.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

csv_path = Path(__file__).with_name("exam_topics.csv")
with csv_path.open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        exam = row["exam"].strip()
        topic = row["topic"].strip()
        cur.execute(
            "INSERT OR IGNORE INTO topics (exam, name) VALUES (?, ?)",
            (exam, topic),
        )

conn.commit()
conn.close()
