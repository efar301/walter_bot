import os

import discord
from discord import app_commands
from discord.ext import commands

from ..config import GUILD_ID, EXAMS, EXAM_CHOICES
from ..db import table_exists, fetch_random, fetch_by_number

class ExamsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="q", description="Get a random or specific exam question.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
        number="Optional question number. Leave blank for a random question.",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def q(self, ctx: commands.Context, exam: str, number: int | None = None):
        exam_key = exam.lower()
        table = EXAMS.get(exam_key)
        if table is None:
            await ctx.send(f"Exam must be one of: {EXAMS.keys()}")
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

async def setup(bot: commands.Bot):
    await bot.add_cog(ExamsCog(bot))
