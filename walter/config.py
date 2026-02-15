import os
from discord import app_commands

DB_PATH = os.getenv("EXAM_DB_PATH", "../sql/exam_db.sqlite")
GUILD_ID = int(os.getenv("WALTER_GUILD_ID", "1467999486403018824"))

EXAMS = {"p": "exam_p", "fm": "exam_fm", "fam": "exam_fam", "srm": "exam_srm"}
EXAM_CHOICES = [
    app_commands.Choice(name="P", value="p"),
    app_commands.Choice(name="FM", value="fm"),
    app_commands.Choice(name="FAM", value="fam"),
    app_commands.Choice(name="SRM", value="srm"),
]
