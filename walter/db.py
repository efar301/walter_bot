import aiosqlite

from .config import DB_PATH

async def fetch_one(query: str, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            return await cur.fetchone()

async def table_exists(table: str) -> bool:
    row = await fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return row is not None

async def fetch_random(table: str):
    row = await fetch_one(f"SELECT COUNT(*) AS n FROM {table}")
    n = int(row["n"])
    if n == 0:
        return None
    import random
    offset = random.randrange(n)
    return await fetch_one(
        f"SELECT number, question_dir, solution FROM {table} LIMIT 1 OFFSET ?",
        (offset,),
    )

async def fetch_by_number(table: str, num: int):
    return await fetch_one(
        f"SELECT number, question_dir, solution FROM {table} WHERE number=?",
        (num,),
    )
