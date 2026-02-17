import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

class WalterBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.load_extension("walter.cogs.exams")
        await self.load_extension("walter.cogs.help")
        await self.load_extension("walter.cogs.user_stats")
        await self.load_extension("walter.cogs.events")

        from .config import GUILD_ID

        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = WalterBot(command_prefix="/", intents=intents, help_command=None)
