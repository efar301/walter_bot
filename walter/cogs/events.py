import datetime as dt
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from ..config import CHANNEL_IDS, ROLE_IDS, SEND_TIMES, TIMEZONE, GUILD_ID
from ..read_sheet import read_weekly_events_async, read_agenda_async

tz = ZoneInfo(TIMEZONE)

def has_any_role_ids(*role_ids):
    async def predicate(ctx):
        return any(role.id in role_ids for role in ctx.author.roles)
    return commands.check(predicate)

def in_channel(channel_id):
    async def predicate(ctx):
        return ctx.channel.id == channel_id
    return commands.check(predicate)

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.weekly_announcement.start()
        self.daily_agenda.start()

    def cog_unload(self) -> None:
        self.weekly_announcement.cancel()
        self.daily_agenda.cancel()



    @tasks.loop(time=dt.time(hour=SEND_TIMES["EVENTS"]["hour"], minute=SEND_TIMES["EVENTS"]["minute"], tzinfo=tz))
    async def weekly_announcement(self):
        now = dt.datetime.now(tz)
        if now.weekday() != SEND_TIMES["EVENTS"]["weekday"]:
            return
        
        channel = self.bot.get_channel(CHANNEL_IDS["EVENTS"])
        if channel is None:
            channel = await self.bot.fetch_channel(CHANNEL_IDS["EVENTS"])

        weekly_events = await read_weekly_events_async()
        
        if len(weekly_events) == 0:
            return

        event_word = "events" if len(weekly_events) == 1 else "event"
        msg = f"**Hello future actuaries! This week we have {len(weekly_events)} {event_word}!**\n"

        for event in weekly_events:
            name, date, time, location, notes = event
            msg += f"\n"
            msg += f"**{name}** - {date} @ {time}\n"
            msg += f"What's happening: {notes}\n"
            msg += f"Location: {location}\n"

        msg += f"\n"
        msg += f"@everyone"
        await channel.send(msg)
        return

    @weekly_announcement.before_loop
    async def before_weekly(self):
        await self.bot.wait_until_ready()

    #@tasks.loop(time=dt.time(hour=SEND_TIMES["AGENDA"]["hour"], minute=SEND_TIMES["AGENDA"]["minute"], tzinfo=tz))
    @tasks.loop(seconds=30)
    async def daily_agenda(self):

        channel = self.bot.get_channel(CHANNEL_IDS["AGENDA"])
        if channel is None:
            channel = await self.bot.fetch_channel(CHANNEL_IDS["AGENDA"])

        agenda = await read_agenda_async()
        
        if len(agenda) == 0:
            return
        
        msg = f"**Things that need to be done:**\n"
        
        for event in agenda:
            name, date, time, details = event
            
            at = "@" if time != "" else ""
            dash = "-" if date != "" else ""

            msg += f"\n"
            msg += f"**{name}** {dash} {date} {at} {time}\n"
            msg += f"{details}"

        msg += f"\n"
        msg += f"<@${ROLE_IDS["OFFICER"]}>"

        await channel.send(msg)
        return


    @daily_agenda.before_loop
    async def before_agenda(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="agenda", description="Get things on officer agenda")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @has_any_role_ids(ROLE_IDS["OFFICER"])
    @in_channel(CHANNEL_IDS["AGENDA"])
    async def agenda(self, ctx: commands.Context):
        if ctx.interaction:
            await ctx.defer()

        agenda = await read_agenda_async()

        if len(agenda) == 0:
            ctx.send("Nothing upcoming soon.")
            return

        msg = f"**Things that need to be done:**\n"
        
        for event in agenda:
            name, date, time, details = event
            
            at = "@" if time != "" else ""
            dash = "-" if date != "" else ""

            msg += f"\n"
            msg += f"**{name}** {dash} {date} {at} {time}\n"
            msg += f"{details}\n"

        # msg += f"\n"
        # msg += f"<@${ROLE_IDS["OFFICER"]}>"

        await ctx.send(msg)
        return

async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
