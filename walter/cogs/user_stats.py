import os

import discord
from discord import app_commands
from discord.ext import commands

# todo: create new db function to collect stats per user
from ..config import GUILD_ID, EXAMS, EXAM_CHOICES
from ..db import table_exists, fetch_user_topic_stats, fetch_exam_topics, fetch_user_exam_totals, update_user_stat_decay

class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="userstats", description="Get statisctics for a specific user")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
        topics="Which topics? (leave empty for all)",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def userstats(self, ctx: commands.Context, exam: str, topics: str | None = None):
        exam_key = exam.lower()
        table = EXAMS.get(exam_key)
        if table is None:
            await ctx.send(f"Exam must be one of: {EXAMS.keys()}")
            return

        if not await table_exists(table):
            await ctx.send(f"Table `{table}` doesn't exist yet.")
            return
        
        topic_stats = await(fetch_user_topic_stats(ctx.author.id, exam, topics))
        if not topic_stats:
            await ctx.send("No problems for this topic attempted yet.")
            return

        reply = f"**Exam {exam.upper()} Stats**\n"
        for topic_stat in topic_stats:
            reply += f"**{topic_stat[0].upper()}**: {topic_stat[1]} correct / {topic_stat[2]} attempted | {topic_stat[3] * 100}% correct\n"
        await ctx.send(reply.strip())

    @userstat.autocomplete("topics")
    async def userstat_topics_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        exam = getattr(interaction.namespace, "exam", None)
        if exam is None:
            return []
        if hasattr(exam, "value"):
            exam = exam.value
        topics = await fetch_exam_topics(str(exam), current)
        return [app_commands.Choice(name=topic, value=topic) for topic in topics]

    @commands.hybrid_command(name="mastery", description="Get mastery for a specific exam.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def mastery(self, ctx: commands.Context, exam: str):
        table = EXAMS.get(exam)
        correct, attempted, total = await fetch_user_exam_totals(ctx.author.id, exam, table)
        await ctx.send("" \
                 f"**Exam {exam.upper()} Statistics**\n"
                 f"Total Correct: {correct}\n"
                 f"Total Attempted: {attempted}\n"
                 f"Percent Correct: {round(correct / total, 2) * 100}%"
                 )

    @commands.hybrid_command(name="statdecay", description="Enable or disable stat decay (your correctly answered questions become wrong after 30 days)")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        value="True or False?",
    )
    async def statdecay(self, ctx: commands.Context, value: bool):
        await update_user_stat_decay(ctx.author.id, value)
        await ctx.send(f"Stat decay set to {value}.", ephemeral=True)

    

async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
