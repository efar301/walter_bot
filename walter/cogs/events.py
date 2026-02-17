import datetime as dt
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from ..config import EVENTS_CHANNEL_ID, EVENT_SENT_TIME, TIMEZONE
from ..read_sheet import read_weekly_events_async

tz = ZoneInfo(TIMEZONE)

class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.weekly_announcement.start()

    def cog_unload(self) -> None:
        self.weekly_announcement.cancel()

    @tasks.loop(time=dt.time(hour=EVENT_SENT_TIME["hour"], minute=EVENT_SENT_TIME["minute"], tzinfo=tz))
    async def weekly_announcement(self):
        now = dt.datetime.now(tz)
        if now.weekday() != EVENT_SENT_TIME["weekday"]:
            return
        
        channel = self.bot.get_channel(EVENTS_CHANNEL_ID)
        if channel is None:
            channel = await self.bot.fetch_channel(EVENTS_CHANNEL_ID)

        weekly_events = await read_weekly_events_async()
        
        if len(weekly_events) == 0:
            return

        event_word = "events" if len(weekly_events) == 1 else "event"
        msg = f"**Hello future actuaries! This week we have {len(weekly_events)} {event_word}!**\n"

        for event in weekly_events:
            name, date, time, location, notes = event
            msg += f"\n"
            msg += f"{name} - {date} @ {time}\n"
            msg += f"What's happening: {notes}\n"
            msg += f"Location: {location}\n"
        await channel.send(msg)
        return

    @weekly_announcement.before_loop
    async def before_weekly(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))