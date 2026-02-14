from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

from ..config import GUILD_ID

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _build_help_embed(self) -> discord.Embed:
        by_cog: dict[str, list[str]] = defaultdict(list)
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            if not getattr(cmd, "app_command", None):
                continue

            cog_name = cmd.cog_name or "Other"
            desc = (
                cmd.app_command.description
                or cmd.description
                or cmd.brief
                or "No description."
            )
            params = [
                f"<{p.name}>" if p.required else f"[{p.name}]"
                for p in cmd.app_command.parameters
            ]
            usage = " ".join([f"/{cmd.name}"] + params).strip()
            by_cog[cog_name].append(f"`{usage}` — {desc}")

        embed = discord.Embed(
            title="Walter Commands",
            description="Slash commands are grouped by feature below.",
            color=discord.Color.blurple(),
        )
        for cog_name in sorted(by_cog.keys()):
            embed.add_field(
                name=cog_name,
                value="\n".join(by_cog[cog_name]),
                inline=False,
            )
        return embed

    @commands.hybrid_command(name="help", description="How to use Walter.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def help(self, ctx: commands.Context):
        embed = self._build_help_embed()
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
