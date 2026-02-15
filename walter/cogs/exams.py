import os

import discord
from discord import app_commands
from discord.ext import commands

from ..config import GUILD_ID, EXAMS, EXAM_CHOICES
from ..db import (
    add_attempt,
    create_user,
    fetch_by_number,
    fetch_question_topics,
    fetch_random,
    table_exists,
)

class ExamsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    class AnswerButton(discord.ui.Button):
        def __init__(self, label: str, view: "ExamsCog.AnswerView"):
            super().__init__(
                label=label,
                style=discord.ButtonStyle.primary,
                custom_id=f"ans|{view.exam}|{view.question_number}|{label}",
            )
            self.answer_view = view

        async def callback(self, interaction: discord.Interaction):
            user_id = interaction.user.id
            selected = str(self.label).upper()
            correct = 1 if selected == self.answer_view.correct_answer else 0

            await create_user(user_id)
            await add_attempt(
                user_id=user_id,
                exam=self.answer_view.exam,
                question_number=self.answer_view.question_number,
                selected_answer=selected,
                correct=correct,
            )

            verdict = "correct" if correct else "incorrect"
            await interaction.response.send_message(
                f"Recorded: {selected} ({verdict}).",
                ephemeral=True,
            )

    class AnswerView(discord.ui.View):
        def __init__(self, exam: str, question_number: int, correct_answer: str):
            super().__init__(timeout=900)
            self.exam = exam
            self.question_number = question_number
            self.correct_answer = correct_answer.upper()

            for label in ["A", "B", "C", "D", "E"]:
                self.add_item(ExamsCog.AnswerButton(label, self))

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

        topics = await fetch_question_topics(exam_key, qnum)
        topics_text = ", ".join(topics) if topics else "none"

        file = discord.File(img_path, filename=os.path.basename(img_path))
        view = ExamsCog.AnswerView(exam_key, qnum, ans)
        await ctx.send(
            f"**Exam {exam_key.upper()} Question {qnum}**\n"
            f"Topics: ||{topics_text}||\n"
            f"Solution: ||{ans}||",
            file=file,
            view=view,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ExamsCog(bot))
