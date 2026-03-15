import os
import random
from typing import Iterable, Optional

import asyncpg

from .config import DB_PATH

# Allow a dedicated Postgres DSN, but fall back to DB_PATH for minimal changes.
PG_DSN = os.getenv("POSTGRES_URL")

_pool: asyncpg.Pool | None = None


def _normalize_exam_code(exam_or_table: str) -> str:
    exam = (exam_or_table or "").strip()
    exam_lower = exam.lower()
    if exam_lower.startswith("exam_"):
        exam_lower = exam_lower[5:]
    return exam_lower.upper()


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not PG_DSN:
            raise RuntimeError(
                "Postgres DSN not set. Set POSTGRES_DSN/DATABASE_URL or DB_PATH."
            )
        _pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=5)
    return _pool


async def _get_user_id(
    conn: asyncpg.Connection, discord_id: int, create: bool = False
) -> Optional[int]:
    row = await conn.fetchrow(
        "SELECT id FROM users WHERE discord_id = $1",
        discord_id,
    )
    if row:
        return int(row["id"])
    if not create:
        return None

    row = await conn.fetchrow(
        """
        INSERT INTO users (discord_id, stat_decay)
        VALUES ($1, $2)
        ON CONFLICT (discord_id) DO NOTHING
        RETURNING id
        """,
        discord_id,
        False,
    )
    if row:
        return int(row["id"])

    # In case of a race, fetch again.
    row = await conn.fetchrow(
        "SELECT id FROM users WHERE discord_id = $1",
        discord_id,
    )
    return int(row["id"]) if row else None


async def _get_exam_id(conn: asyncpg.Connection, exam_or_table: str) -> Optional[int]:
    code = _normalize_exam_code(exam_or_table)
    if not code:
        return None
    row = await conn.fetchrow(
        "SELECT id FROM exams WHERE code = $1",
        code,
    )
    return int(row["id"]) if row else None


# adds a user to a the user table
async def create_user(user_id: int) -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await _get_user_id(conn, user_id, create=True)


# sets user preference for stat_decay
async def update_user_stat_decay(discord_id: int, stat_decay: bool) -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await _get_user_id(conn, discord_id, create=True)
        await conn.execute(
            """
            UPDATE users
            SET stat_decay = $1
            WHERE discord_id = $2
            """,
            bool(stat_decay),
            discord_id,
        )


async def update_user_stat_decay_period(discord_id, period: str) -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await _get_user_id(conn, discord_id, create=True)
        await conn.execute(
            """
            UPDATE users
            SET decay_time = $1
            WHERE discord_id = $2
            """,
            period,
            discord_id,
        )


# adds users latest question attempt to a attempts table
async def add_attempt(
    user_id: int,
    exam: str,
    question_number: int,
    selected_answer: str,
    correct: int,
) -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        internal_user_id = await _get_user_id(conn, user_id, create=True)
        if internal_user_id is None:
            return

        exam_id = await _get_exam_id(conn, exam)
        if exam_id is None:
            return

        question_row = await conn.fetchrow(
            """
            SELECT id
            FROM questions
            WHERE exam_id = $1 AND question_number = $2
            """,
            exam_id,
            question_number,
        )
        if question_row is None:
            return

        question_id = int(question_row["id"])

        # Preserve previous behavior: one attempt per user/question (latest wins).
        await conn.execute(
            """
            DELETE FROM question_attempts
            WHERE user_id = $1 AND question_id = $2 AND mode = 'single'
            """,
            internal_user_id,
            question_id,
        )

        await conn.execute(
            """
            INSERT INTO question_attempts
                (user_id, question_id, mode, selected_answer, is_correct)
            VALUES
                ($1, $2, 'single', $3, $4)
            """,
            internal_user_id,
            question_id,
            selected_answer.strip().upper(),
            bool(correct),
        )


# fetches a question from an exam table
async def fetch_one_question(query: str, params=()):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *params)


# check if exam exists (used in place of old per-exam tables)
async def table_exists(table: str) -> bool:
    pool = await _get_pool()
    code = _normalize_exam_code(table)
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "SELECT 1 FROM exams WHERE code = $1",
                code,
            )
            return row is not None
        except Exception:
            return False


# gets a random exam question from specified exam table
async def fetch_random(table: str):
    pool = await _get_pool()
    code = _normalize_exam_code(table)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS n
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            WHERE e.code = $1
            """,
            code,
        )
        n = int(row["n"])
        if n == 0:
            return None

        offset = random.randrange(n)
        return await conn.fetchrow(
            """
            SELECT
                q.question_number AS number,
                q.image_path AS question_dir,
                q.solution AS solution
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            WHERE e.code = $1
            ORDER BY q.question_number
            OFFSET $2
            LIMIT 1
            """,
            code,
            offset,
        )


# gets a specific exam question from specified exam
async def fetch_by_number(table: str, num: int):
    pool = await _get_pool()
    code = _normalize_exam_code(table)
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT
                q.question_number AS number,
                q.image_path AS question_dir,
                q.solution AS solution
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            WHERE e.code = $1 AND q.question_number = $2
            """,
            code,
            num,
        )


# gets a random exam question from specified exam by topic
async def fetch_by_topic(table: str, exam: str, topic: str):
    pool = await _get_pool()
    code = _normalize_exam_code(exam or table)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS n
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            JOIN question_topics qt ON qt.question_id = q.id
            JOIN topics t ON t.id = qt.topic_id
            WHERE e.code = $1 AND t.name = $2
            """,
            code,
            topic,
        )
        n = int(row["n"])
        if n == 0:
            return None

        offset = random.randrange(n)
        return await conn.fetchrow(
            """
            SELECT
                q.question_number AS number,
                q.image_path AS question_dir,
                q.solution AS solution
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            JOIN question_topics qt ON qt.question_id = q.id
            JOIN topics t ON t.id = qt.topic_id
            WHERE e.code = $1 AND t.name = $2
            ORDER BY q.question_number
            OFFSET $3
            LIMIT 1
            """,
            code,
            topic,
            offset,
        )


# gets question topics for an exam
async def fetch_question_topics(exam: str, question_number: int):
    code = _normalize_exam_code(exam)
    sql = """
    SELECT t.name
    FROM questions q
    JOIN exams e ON e.id = q.exam_id
    JOIN question_topics qt ON qt.question_id = q.id
    JOIN topics t ON t.id = qt.topic_id
    WHERE e.code = $1 AND q.question_number = $2
    ORDER BY t.name
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, code, question_number)
        return [row["name"] for row in rows]


# returns the exam stats
async def fetch_user_exam_totals(user_id: int, exam: str, table: str):
    pool = await _get_pool()
    code = _normalize_exam_code(exam or table)
    async with pool.acquire() as conn:
        internal_user_id = await _get_user_id(conn, user_id, create=False)
        if internal_user_id is None:
            return (0, 0, 0)

        correct_row = await conn.fetchrow(
            """
            WITH latest AS (
                SELECT DISTINCT ON (qa.question_id)
                    qa.question_id,
                    qa.is_correct
                FROM question_attempts qa
                JOIN questions q ON q.id = qa.question_id
                JOIN exams e ON e.id = q.exam_id
                WHERE qa.user_id = $1 AND e.code = $2 AND qa.mode = 'single'
                ORDER BY qa.question_id, qa.created_at DESC
            )
            SELECT
                COUNT(*) FILTER (WHERE is_correct) AS correct_count,
                COUNT(*) AS attempted_count
            FROM latest
            """,
            internal_user_id,
            code,
        )

        total_row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS total_count
            FROM questions q
            JOIN exams e ON e.id = q.exam_id
            WHERE e.code = $1
            """,
            code,
        )
        return (
            int(correct_row["correct_count"] or 0),
            int(correct_row["attempted_count"] or 0),
            int(total_row["total_count"] or 0),
        )


async def fetch_exam_topics(exam: str, query: str = "", limit: int = 25):
    code = _normalize_exam_code(exam)
    query = (query or "").strip()
    like = f"%{query}%"
    sql = """
    SELECT t.name
    FROM topics t
    JOIN exams e ON e.id = t.exam_id
    WHERE e.code = $1 AND t.name ILIKE $2
    ORDER BY t.name
    LIMIT $3
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, code, like, limit)
        return [row["name"] for row in rows]


# gets user exam stats per topic
async def fetch_user_topic_stats(
    discord_id: int,
    exam: str,
    topics: Optional[Iterable[str] | str] = None,
):
    code = _normalize_exam_code(exam)
    if topics is None:
        topic_list: list[str] = []
    elif isinstance(topics, str):
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    else:
        topic_list = [str(t).strip() for t in topics if str(t).strip()]

    pool = await _get_pool()
    async with pool.acquire() as conn:
        internal_discord_id = await _get_user_id(conn, discord_id, create=False)
        if internal_discord_id is None:
            return []

        params: list[object] = [internal_discord_id, code]
        topic_filter = ""
        if topic_list:
            placeholders = ", ".join(f"${i}" for i in range(3, 3 + len(topic_list)))
            topic_filter = f" AND t.name IN ({placeholders})"
            params.extend(topic_list)

        sql = f"""
        WITH latest AS (
            SELECT DISTINCT ON (qa.question_id)
                qa.question_id,
                qa.is_correct
            FROM question_attempts qa
            JOIN questions q ON q.id = qa.question_id
            JOIN exams e ON e.id = q.exam_id
            WHERE qa.user_id = $1 AND e.code = $2 AND qa.mode = 'single'
            ORDER BY qa.question_id, qa.created_at DESC
        )
        SELECT
            t.name,
            SUM(CASE WHEN l.is_correct THEN 1 ELSE 0 END) AS correct_count,
            COUNT(*) AS total_count,
            (SUM(CASE WHEN l.is_correct THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) AS pct_correct
        FROM latest l
        JOIN question_topics qt ON qt.question_id = l.question_id
        JOIN topics t ON t.id = qt.topic_id
        JOIN exams e ON e.id = t.exam_id
        WHERE e.code = $2{topic_filter}
        GROUP BY t.name
        """

        return await conn.fetch(sql, *params)
