import os

import discord
from discord import app_commands
from discord.ext import commands

# todo: create new db function to collect stats per user
from ..config import EXAM_CHOICES, EXAMS, GUILD_ID, STAT_DECAY_CHOICES
from ..postgresdb import (
    fetch_exam_topics,
    fetch_user_exam_totals,
    fetch_user_topic_stats,
    table_exists,
    update_user_stat_decay,
    update_user_stat_decay_period,
)
from ..sheet_functions import write_question_async


class UserCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="userstats", description="Get statisctics for a specific user"
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
        topics="Which topics? (leave empty for all)",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def userstats(
        self, ctx: commands.Context, exam: str, topics: str | None = None
    ):
        exam_key = exam.lower()
        table = EXAMS.get(exam_key)

        if table is None:
            await ctx.send(f"Exam must be one of {EXAMS.keys()}")
            return

        if not await table_exists(table):
            await ctx.send(f"Table `{table}` doesn't exist yet.")
            return

        topic_stats = await fetch_user_topic_stats(ctx.author.id, exam, topics)
        if not topic_stats:
            await ctx.send("No problems for this topic attempted yet.")
            return

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s stats for Exam {exam}",
            color=discord.Color.blurple(),
        )

        for stat in topic_stats:
            pct = round(stat[3], 2) * 100
            embed.add_field(
                name=stat[0].upper(),
                value=f"\n{stat[1]} correct / {stat[2]} attempted\n{pct}% correct",
                inline=True,
            )
        await ctx.send(embed=embed)
        return


    @userstats.autocomplete("topics")
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

    @commands.hybrid_command(
        name="mastery", description="Get mastery for a specific exam."
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?",
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def mastery(self, ctx: commands.Context, exam: str):
        table = EXAMS.get(exam)
        
        if table is None:
            await ctx.send(f"Exam must be one of {EXAMS.keys()}")
            return
            
        correct, attempted, total = await fetch_user_exam_totals(
            ctx.author.id, exam, table
        )
        
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s mastery for Exam {exam}",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="Total Correct",
            value=f"{correct}",
            inline=True
        )
        embed.add_field(
            name="Total Attempted",
            value=f"{attempted}",
            inline=True
        )
        embed.add_field(
            name="Total Questions in bank",
            value=f"{total}",
            inline=True
        )
        embed.add_field(
            name="Percent Correct",
            value=f"{round(correct / total, 2) * 100}%",
            inline=True
        )

        await ctx.send(embed=embed)
        return

    @commands.hybrid_command(
        name="statdecay",
        description="Enable or disable stat decay (your correctly answered questions become wrong after a period)",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(value="True or False?", period="How often to decay stats")
    @app_commands.choices(period=STAT_DECAY_CHOICES)
    async def statdecay(self, ctx: commands.Context, value: bool, period: str):
        await update_user_stat_decay(ctx.author.id, value)
        await update_user_stat_decay_period(ctx.author.id, period)
        await ctx.send(
            f"Stat decay set to {value}, decay period is {period}", ephemeral=True
        )

    @commands.hybrid_command(
        name="question_help",
        description="Tell us a specific question you want covered next meeting (put 0 if its a non exam question)",
    )
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(
        exam="Which exam?", question_number="Question Number", name="Your name"
    )
    @app_commands.choices(exam=EXAM_CHOICES)
    async def question_help(
        self, ctx: commands.Context, exam: str, question_number: int, name: str
    ):
        sheet_name = f"{exam.upper()} Study Calendar"
        appended_question = f"Question {question_number} ({name})"

        await write_question_async(sheet_name, appended_question)
        await ctx.send("Question submitted, thanks!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UserCog(bot))
