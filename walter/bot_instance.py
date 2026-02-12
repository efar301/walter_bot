import discord
from discord.ext import client

ASC_SERVER_ID = 1467999486403018824

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)
