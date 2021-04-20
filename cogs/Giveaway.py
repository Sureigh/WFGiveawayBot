# -*- coding: utf-8 -*-

import aiosqlite
import discord
from discord.ext import commands
from discord_slash import cog_ext as slash
from googleapiclient.discovery import build
from google.oauth2 import service_account

from config import GOOGLE_API_CREDS

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

    # TODO: Make guild_ids sync with internal config system
    @slash.cog_slash(name="platcount", description="Check how much plat you've donated to the server.",
                     guild_ids=[465910450819694592, 487093399741267968])
    async def plat_count(self, ctx):
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

        values = await self.bot.loop.run_in_executor(None, grab_sheet)

        # TODO: unfuck
        # Returns a dict of dicts, where user ID is the key and returns a dict of plat value
        values = [value.get("values") for value in values]
        values = {int(*user): {"plat": int(*plat), "title": str(*title), "rank": rank}
                  for rank, (user, plat, title) in enumerate(zip(*values), start=1)}

        await ctx.send(str(values)[:2000])

        """message = [
            "**Total donated platinum:**",
            f"{plat} platinum",
            "\n",
            title,
            # f"{} in leaderboard"
        ]
        embed = discord.Embed(title=message[0], description=message[1],
                              color=await bot.color(ctx))
        # await ctx.send(message, embed=embed, hidden=hidden)
        await ctx.send(f"{await bot.ranks(ctx)}\n{results}", hidden=hidden)

        # Fails if the user ID is not on the sheet

            await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?")"""

    @slash.cog_slash(name="query", guild_ids=[465910450819694592])
    async def test(self, ctx, query):
        await ctx.defer()
        async with aiosqlite.connect(self.bot.db) as db:
            await db.execute(query)
            await db.commit()
        await ctx.send("<:RemNice:465919491272867852>")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # reaction should be the tada emote, duh
        # the reaction should also be added on a valid giveaway

        # if all(reaction == "the tada emote idk", ):
        pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
