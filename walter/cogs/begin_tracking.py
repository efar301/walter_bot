import os

import discord
from discord import app_commands
from discord.ext import commands

from ..config import GUILD_ID
from ..db import add_user

class AddUserCob