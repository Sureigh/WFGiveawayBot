# -*- coding: utf-8 -*-

import aiosqlite
from googleapiclient.discovery import build
from google.oauth2 import service_account
from discord.ext import commands
from discord_slash import cog_ext as slash

import config

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
                    credentials=service_account.Credentials.from_service_account_file(config.GOOGLE_API_CREDS,
                                                                                      scopes=SCOPES)
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
                            ON CONFLICT (user)
                            DO UPDATE SET plat=sheet.plat, rank=sheet.rank, title=sheet.title;
                        """, values)
                await db.commit()

        bot.cache_sheet = cache_sheet

    @slash.cog_slash(name="update_sheet", description="Force update the cached spreadsheet.",
                     guild_ids=config.guilds)
    async def update_sheet(self, ctx):
        hidden = await ctx.bot.hidden(ctx)
        await ctx.defer(hidden)
        if ctx.author.guild_permissions.manage_messages:
            await ctx.send("<a:RemThonk:696351936051413062> Okay, give me a moment...", hidden=hidden)
            await ctx.bot.cache_sheet()
            await ctx.send(content="👍", hidden=hidden)
        else:
            await ctx.send("Sorry, you must be a moderator to perform this action.", hidden=hidden)


def setup(bot):
    bot.add_cog(Sheet(bot))
