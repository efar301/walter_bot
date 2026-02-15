import csv
from pathlib import Path

from walter.config import DB_PATH

import sqlite3

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

def load_topic_map():
    cur.execute("SELECT topic_id, exam, name FROM topics")
    rows = cur.fetchall()
    return {(exam, name): topic_id for (topic_id, exam, name) in rows}

topic_map = load_topic_map()

labels_dir = Path(__file__).parent / "labeled_questions"
label_files = {
    "p": labels_dir / "p_labelled.csv",
    "fm": labels_dir / "fm_labelled.csv",
    "srm": labels_dir / "srm_labelled.csv",
}

for exam, csv_path in label_files.items():
    if not csv_path.exists():
        print(f"missing: {csv_path}")
        continue
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topics = row["topics"]
            question_num = int(row["question_num"])
            topic_list = [t.strip() for t in topics.split("|") if t.strip()]

            for topic in topic_list:
                topic_id = topic_map.get((exam, topic))
                if topic_id is None:
                    raise ValueError(f"Topic not found: exam={exam} topic={topic}")
                cur.execute(
                    "INSERT OR IGNORE INTO question_topics (exam, question_number, topic_id) VALUES (?, ?, ?)",
                    (exam, question_num, topic_id),
                )

conn.commit()
conn.close()
