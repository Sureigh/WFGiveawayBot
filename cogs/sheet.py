# -*- coding: utf-8 -*-

import aiosqlite
from googleapiclient.discovery import build
from google.oauth2 import service_account
from discord.ext import commands

import configs

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Sheet(commands.Cog):
    """Manages inserting and reading data from Google Sheets."""

    def __init__(self, bot):
        self.bot = bot

        async def cache_sheet():
            # Thank you, GSheets. I hate you.
            def grab_sheet():
                service = build(
                    'sheets', 'v4',
                    credentials=service_account.Credentials.from_service_account_file(configs.GOOGLE_API_CREDS,
                                                                                      scopes=SCOPES)
                )
                result = service.spreadsheets().values().batchGet(
                    spreadsheetId="14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc",
                    ranges=["A2:A", "C2:C", "E2:E"]
                ).execute()

                return result.get("valueRanges")

            # Thanks Ava :verycool:
            values = [value.get("values") for value in await self.bot.loop.run_in_executor(None, grab_sheet)]
            values = [(int(*user), int(*plat), rank, str(*title))
                      for rank, (user, plat, title) in enumerate(zip(*values), start=1)]

            async with aiosqlite.connect(configs.DATABASE_NAME) as db:
                await db.executemany("""
                            INSERT INTO sheet
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT (user)
                            DO UPDATE SET plat=sheet.plat, rank=sheet.rank, title=sheet.title;
                        """, values)
                await db.commit()

        bot.cache_sheet = cache_sheet

    @commands.command(name="update_sheet", description="Force updates the cached spreadsheet.")
    async def update_sheet(self, ctx):
        if not ctx.author.guild_permissions.manage_messages:
            raise commands.MissingPermissions
        await ctx.send("<a:RemThonk:696351936051413062> Okay, give me a moment...")
        await ctx.bot.cache_sheet()
        await ctx.send("Successfully updated spreadsheet cache. 👍")


def setup(bot):
    bot.add_cog(Sheet(bot))
