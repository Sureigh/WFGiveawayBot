# -*- coding: utf-8 -*-

from googleapiclient.discovery import build
from google.oauth2 import service_account
from discord.ext import commands, tasks
import aiosqlite

from config import GOOGLE_API_CREDS

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
TIMER = 30.0


class Timers(commands.Cog):
    """A cog that manages an hourly timer to cache the giveaway spreadsheet, and start giveaway timers."""

    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways_and_cache.start()

    def cog_unload(self):
        self.check_giveaways_and_cache.cancel()

    # TODO: Turn this into a command invocation instead so it can also be triggered manually
    @tasks.loop(minutes=TIMER)
    async def check_giveaways_and_cache(self):
        # Sheet caching
        # Thank you, GSheets. I hate you.
        def grab_sheet():
            service = build(
                'sheets', 'v4',
                credentials=service_account.Credentials.from_service_account_file(GOOGLE_API_CREDS, scopes=SCOPES)
            )
            result = service.spreadsheets().values().batchGet(
                spreadsheetId="14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc",
                ranges=["A2:A", "C2:C", "E2:E"]
            ).execute()

            return result.get("valueRanges")

        # Thanks Ava :verycool:
        values = await self.bot.loop.run_in_executor(None, grab_sheet)
        values = [value.get("values") for value in values]
        values = [(int(*user), int(*plat), rank, str(*title))
                  for rank, (user, plat, title) in enumerate(zip(*values), start=1)]

        async with aiosqlite.connect(self.bot.db) as db:
            await db.executemany("""
                INSERT INTO sheet
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user) DO NOTHING,
                ON CONFLICT (plat, rank, title) DO UPDATE (plat, rank, title);
            """, values)
            await db.commit()

        # Giveaway timer check
        # TODO: 'if a timer expires within 30 min, start a loop to end it at that time'


def setup(bot):
    bot.add_cog(Timers(bot))
