import os

import discord
from discord import app_commands
from discord.ext import commands

# todo: create new db function to collect stats per user
from ..config import GUILD_ID, EXAMS, EXAM_CHOICES
from ..db import table_exists


# EXAMS = {"p": "exam_p", "fm": "exam_fm", "fam": "exam_fam", "srm": "exam_srm"}
# EXAM_CHOICES = [
#     app_commands.Choice(name="P", value="p"),
#     app_commands.Choice(name="FM", value="fm"),
#     app_commands.Choice(name="FAM", value="fam"),
#     app_commands.Choice(name="SRM", value="srm"),
# ]

class UserStatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="userstat", description="Get statisctics for a specific user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
        topic="Which topics?",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def userstat(self, ctx: commands.Context, exam: str, topics: str | None = None):
        exam_key = exam.lower()
        table = EXAMS.get(exam_key)
        if table is None:
            await ctx.send(f"Exam must be one of: {EXAMS.keys()}")
            return

        if not await table_exists(table):
            await ctx.send(f"Table `{table}` doesn't exist yet.")
            return
    
        
