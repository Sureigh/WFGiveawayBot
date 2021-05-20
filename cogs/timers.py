# -*- coding: utf-8 -*-

from discord.ext import commands, tasks
from sqlite3 import PARSE_DECLTYPES
import aiosqlite
import datetime

import asyncio

import configs


class Timers(commands.Cog):
    """A cog that manages an hourly timer to cache the giveaway spreadsheet, and start giveaway timers."""

    def __init__(self, bot):
        self.bot = bot
        # TODO: bot.loop.run_until_complete(self.check_expired_giveaways())
        self.check_timers.start()

    def cog_unload(self):
        self.check_timers.cancel()

    """@staticmethod
    async def check_expired_giveaways():
        ""
        Although rare, a bot outage is definitely a possibility.
        This method tries to check if any past giveaways that should have ended is not ended, and will forcibly do so.
        ""
        async with aiosqlite.connect(configs.DATABASE_NAME, detect_types=PARSE_DECLTYPES) as db:
            async with db.execute(
                "SELECT giveaway FROM giveaways WHERE ? > g_end AND ended = 0 ORDER BY end ASC;",
                (datetime.datetime.utcnow().timestamp(),)
            ) as cursor:
                async for g in cursor:
                    await g[0].end()
                    await db.execute("UPDATE giveaways SET ended = 1 WHERE giveaway = ?", (g[0],))
            await db.commit()"""

    @tasks.loop(minutes=configs.TIMER)
    async def check_timers(self):
        bot = self.bot

        # Caches GSheets data
        await bot.cache_sheet()

        # Giveaway timer check
        async with aiosqlite.connect(configs.DATABASE_NAME, detect_types=PARSE_DECLTYPES) as db:
            db.row_factory = aiosqlite.Row

            async def giveaway(_now, _later, g):
                await asyncio.sleep(_later - _now)
                await g.end()

            for guild in bot.guilds:
                # Just to make sure we don't miss out on anything, the time overlaps slightly.
                # It may decrease efficiency but it'll be 99.97% safer that way. I hope.
                now = datetime.datetime.utcnow()
                later = now + datetime.timedelta(minutes=configs.TIMER * 1.25)
                async with db.execute("""
                    SELECT * FROM giveaways WHERE g_end BETWEEN ? AND ? AND ended = 0 AND guild = ? ORDER BY g_end ASC;
                """, (now.timestamp(), later.timestamp(), guild.id)) as cursor:
                    # TODO: I have no idea how efficient this is, could go back to original idea if it sucks
                    await asyncio.gather(*[giveaway(now.timestamp(), row["g_end"], row["giveaway"])
                                           async for row in cursor])

        # Disqualified timer check
        # TODO: Same as above


def setup(bot):
    bot.add_cog(Timers(bot))
