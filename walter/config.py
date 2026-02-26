import os
from discord import app_commands

DB_PATH = os.getenv("EXAM_DB_PATH", "../sql/exam_db.sqlite")
GUILD_ID = int(os.getenv("WALTER_GUILD_ID", "1467999486403018824"))


ROLE_IDS = {"OFFICER": 1467999486403018825}
CHANNEL_IDS = {"EVENTS": 1467999487380426796, "AGENDA": 1476329536793612412}

EXAMS = {"p": "exam_p", "fm": "exam_fm", "fam": "exam_fam", "srm": "exam_srm"}
EXAM_CHOICES = [
    app_commands.Choice(name="P", value="p"),
    app_commands.Choice(name="FM", value="fm"),
    app_commands.Choice(name="FAM", value="fam"),
    app_commands.Choice(name="SRM", value="srm"),
]


TIMEZONE = "America/Los_Angeles"

SEND_TIMES = {
    "EVENTS": {"weekday": 0, "hour": 9, "minute": 0},
    "AGENDA": {"hour": 9, "minute": 0}
}