import aiosqlite
from datetime import datetime, timezone
from typing import Iterable, Optional

from .config import DB_PATH

# adds a user to a the user table
async def create_user(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        created_at = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, stat_decay, created_at) VALUES (?, ?, ?)",
            (user_id, 0, created_at,)
        )
        await db.commit()

# sets user preference for stat_decay
async def update_user_stat_decay(user_id: int, stat_decay: bool) -> None:
    updated_val = 1 if stat_decay == True else 0
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE users
            SET stat_decay = ?
            WHERE user_id = ?
            """,
            (updated_val, user_id,)
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

# gets a random exam question from specified exam by topic
async def fetch_by_topic(table: str, exam: str, topic: str):
    # count matching questions
    row = await fetch_one_question(
        f"""
        SELECT COUNT(*) AS n
        FROM {table} e
        JOIN question_topics qt
            ON qt.exam = ? AND qt.question_number = e.number
        JOIN topics t
            ON qt.topic_id = t.topic_id
        WHERE t.name = ?
        """,
        (exam, topic),
    )
    n = int(row["n"])
    if n == 0:
        return None

    import random
    offset = random.randrange(n)
    return await fetch_one_question(
        f"""
        SELECT e.number, e.question_dir, e.solution
        FROM {table} e
        JOIN question_topics qt
            ON qt.exam = ? AND qt.question_number = e.number
        JOIN topics t
            ON qt.topic_id = t.topic_id
        WHERE t.name = ?
        LIMIT 1 OFFSET ?
        """,
        (exam, topic, offset),
    )

# gets question topics for an exam
async def fetch_question_topics(exam: str, question_number: int):
    sql = """
    SELECT t.name
    FROM question_topics qt
    JOIN topics t ON qt.topic_id = t.topic_id
    WHERE qt.exam = ? AND qt.question_number = ?
    ORDER BY t.name
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, (exam, question_number)) as cur:
            rows = await cur.fetchall()
            return [row[0] for row in rows]

# returns the exam stats
async def fetch_user_exam_totals(user_id: int, exam: str, table: str):
    exam = exam.lower()
    correct_row = await fetch_one_question(
        """
        SELECT COALESCE(SUM(correct), 0) AS correct_count,
               COUNT(*) AS attempted_count
        FROM attempts
        WHERE user_id = ? AND exam = ?
        """,
        (user_id, exam),
    )
    total_row = await fetch_one_question(
        f"SELECT COUNT(*) AS total_count FROM {table}"
    )
    return (
        int(correct_row["correct_count"]),
        int(correct_row["attempted_count"]),
        int(total_row["total_count"]),
    )

async def fetch_exam_topics(exam: str, query: str = "", limit: int = 25):
    exam = exam.lower()
    query = (query or "").strip()
    like = f"%{query}%"
    sql = """
    SELECT name
    FROM topics
    WHERE exam = ? AND name LIKE ?
    ORDER BY name
    LIMIT ?
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, (exam, like, limit)) as cur:
            rows = await cur.fetchall()
            return [row[0] for row in rows]

# gets user exam stats per topic
async def fetch_user_topic_stats(
    user_id: int,
    exam: str,
    topics: Optional[Iterable[str] | str] = None,
):
    exam = exam.lower()
    if topics is None:
        topic_list = []
    elif isinstance(topics, str):
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    else:
        topic_list = [str(t).strip() for t in topics if str(t).strip()]

    sql = """
    SELECT
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

    sql += " GROUP BY t.name;"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, params) as cur:
            return await cur.fetchall()

