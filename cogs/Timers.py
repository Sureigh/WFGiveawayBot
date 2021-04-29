# -*- coding: utf-8 -*-

from discord.ext import commands, tasks

TIMER = 30.0

class Timers(commands.Cog):
    """A cog that manages an hourly timer to cache the giveaway spreadsheet, and start giveaway timers."""

    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways_and_cache.start()

    def cog_unload(self):
        self.check_giveaways_and_cache.cancel()

    @tasks.loop(minutes=TIMER)
    async def check_giveaways_and_cache(self):
        await self.bot.cache_sheet()

        # Giveaway timer check
        # TODO: 'if a timer expires within 30 min, start a loop to end it at that time'


def setup(bot):
    bot.add_cog(Timers(bot))
