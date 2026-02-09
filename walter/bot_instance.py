import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True  # requires Message Content Intent enabled in Dev Portal

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

