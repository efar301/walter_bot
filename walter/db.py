import aiosqlite
from datetime import datetime, timezone
from typing import Iterable, Optional

from .config import DB_PATH

# adds a user to a the user table
async def create_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        created_at = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO users (user_id, created_at) VALUES (?, ?)",
            (user_id, created_at,)
            )
        await db.commit()

# adds users latest question attempt to a attempts table
async def add_attempt(user_id: int, exam: str, question_number: int, selected_answer: str, correct: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        created_at = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR REPLACE INTO attempts (user_id, exam, question_number, selected_answer, correct, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, exam, question_number, selected_answer, correct, created_at,)
            )
        await db.commit()

# fetches a question from an exam table
async def fetch_one_question(query: str, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            return await cur.fetchone()

# check if exam table exists in database
async def table_exists(table: str) -> bool:
    row = await fetch_one_question(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return row is not None

# gets a random exam question from specified exam table
async def fetch_random(table: str):
    row = await fetch_one_question(f"SELECT COUNT(*) AS n FROM {table}")
    n = int(row["n"])
    if n == 0:
        return None
    import random
    offset = random.randrange(n)
    return await fetch_one_question(
        f"SELECT number, question_dir, solution FROM {table} LIMIT 1 OFFSET ?",
        (offset,),
    )

# gets a specific exam question from specified exam
async def fetch_by_number(table: str, num: int):
    return await fetch_one_question(
        f"SELECT number, question_dir, solution FROM {table} WHERE number=?",
        (num,),
    )

async def fetch_user_topic_stats(
    user_id: int,
    exam: str,
    topics: Optional[Iterable[str]] = None,
):
    exam = exam.lower()
    topic_list = [t.strip() for t in topics] if topics else []

    sql = """
    SELECT
        t.topic_id,
        t.name,
        SUM(CASE WHEN a.correct = 1 THEN 1 ELSE 0 END) AS correct_count,
        COUNT(*) AS total_count,
        (SUM(CASE WHEN a.correct = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) AS pct_correct
    FROM attempts a
    JOIN question_topics qt
        ON a.exam = qt.exam AND a.question_number = qt.question_number
    JOIN topics t
        ON qt.topic_id = t.topic_id
    WHERE a.user_id = ? AND a.exam = ?
    """
    params = [user_id, exam]

    if topic_list:
        placeholders = ", ".join(["?"] * len(topic_list))
        sql += f" AND t.name IN ({placeholders})"
        params.extend(topic_list)

    sql += " GROUP BY t.topic_id, t.name;"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, params) as cur:
            return await cur.fetchall()
