import os

import discord
from discord import app_commands
from discord.ext import commands

# todo: create new db function to collect stats per user
from ..config import GUILD_ID, EXAMS, EXAM_CHOICES
from ..db import table_exists, fetch_user_topic_stats

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="userstat", description="Get statisctics for a specific user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
        topics="Which topics? (leave empty for all)",
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
        
        topic_stats = await(fetch_user_topic_stats(ctx.author.id, exam, topics))
        reply = f"**Exam {exam} Stats**\n"
        for topic_stat in topic_stats:
            reply += f"**{topic_stat[0].upper()}**: {topic_stat[1]} correct / {topic_stat[2]} attempted | {topic_stat[3]}% correct\n"
        await ctx.send(reply.strip())

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
