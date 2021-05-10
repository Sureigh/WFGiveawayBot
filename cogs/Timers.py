# -*- coding: utf-8 -*-

from discord.ext import commands, tasks
import aiosqlite

TIMER = 15.0

class Timers(commands.Cog):
    """A cog that manages an hourly timer to cache the giveaway spreadsheet, and start giveaway timers."""

    def __init__(self, bot):
        self.bot = bot
        self.check_timers.start()

    def cog_unload(self):
        self.check_timers.cancel()

    @tasks.loop(minutes=TIMER)
    async def check_timers(self):
        bot = self.bot

        # Caches GSheets data
        await bot.cache_sheet()

        # Giveaway timer check
        async with aiosqlite.connect(bot.db) as db:
            async with db.execute("""
                SELECT * FROM giveaways
            """) as cursor:
                pass
        # TODO: 'if a timer expires within 30 min, start a loop to end it at that time'

        # Disqualified timer check
        # TODO: Same as above


def setup(bot):
    bot.add_cog(Timers(bot))
