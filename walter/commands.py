import os
import random
import textwrap
import aiosqlite
import discord
from discord.ext import commands

from .bot_instance import bot

DB_PATH = os.getenv("EXAM_DB_PATH", "../sql/exam_db.sqlite")
EXAMS = {"p": "exam_p", "fm": "exam_fm", "fam": "exam_fam", "srm": "exam_srm"}

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

@bot.event
async def on_ready():
    print(f"READY as {bot.user} | message_content={bot.intents.message_content}")

@bot.event
async def on_command_error(ctx, error):
    print("COMMAND ERROR:", repr(error))
    await ctx.send(f"Error: {error}")

# @bot.slash_command(name="whatdoido")
# async def whatdoido(ctx):
#     msg = textwrap.dedent("""
#     I can help study with exams and keep you updated on club events!

#     Some things I can do:
#         1) Send you an exam question/solution
#         2) Provide exam resources (coming soon)
#         3) Track the questions you've gotten right and wrong (coming soon)
#         4) Tell you about upcoming club events (coming soon)

#     Soon, I'll be able to do some other cool stuff that is secret for now.

#     Now, get to studying.
#     """).strip()
#     await ctx.send(msg)

# @bot.slash_command(name="help")
# async def help(ctx):
#     msg = textwrap.dedent("""
#     **How to use walter**

#     1) Bot Features
#         Get a list of things I can do
#         command usage \\whatdoido

#     2) Exam questions
#         You can get either a specific or random SOA exam question along with the solution in a spoiler
#         command usage: \\q {exam_name} {question_num}

#     3) Track practice statistics
#         With a little bit of help on your end, I can track personal and global question statistics, showing the easiest and hardest problems
#         command usage: TBD

#     4) Send exam resources
#         I can send you exam information/resources
#         command usage: TBD

#     5) Update you on club events
#         I can tell you about our next upcoming club events and any other activities planned
#         command usage: TBD
#     """).strip()
#     await ctx.send(msg)

@bot.hybrid_command(name="q")
async def q(ctx: commands.Context, exam: str, number: int | None = None):
    exam_key = exam.lower()
    table = EXAMS.get(exam_key)
    if table is None:
        await ctx.send("Exam must be one of: p, fm, fam, srm.")
        return

    if not await table_exists(table):
        await ctx.send(f"Table `{table}` doesn't exist yet.")
        return

    row = await (fetch_by_number(table, number) if number is not None else fetch_random(table))
    if row is None:
        await ctx.send("No question found.")
        return

    qnum = int(row["number"])
    img_path = row["question_dir"]
    ans = str(row["solution"]).strip().upper()

    if not img_path or not os.path.exists(img_path):
        await ctx.send(f"Exam {table} #{qnum}: image not found at `{img_path}`.")
        return

    file = discord.File(img_path, filename=os.path.basename(img_path))
    await ctx.send(f"**Exam {exam_key.upper()} Question {qnum}**\nSolution: ||{ans}||", file=file)

