# -*- coding: utf-8 -*-

import aiohttp
import aiosqlite
import discord
from discord.ext import commands
from discord_slash import cog_ext as slash

import json


class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

    # TODO: Make guild_ids sync with internal config system
    @slash.cog_slash(name="platcount", description="Check how much plat you've donated to the server.",
                     guild_ids=[465910450819694592])
    async def plat_count(self, ctx):
        bot = self.bot
        hidden = await bot.hidden(ctx)
        await ctx.defer(hidden)

        # TODO: im scrapping all of this god damn it
        async with aiohttp.ClientSession(headers={"X-DataSource-Auth": "true"}) as cs:
            async with cs.get(
                    "https://docs.google.com/spreadsheets/d/"
                    f"14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc/gviz/tq?tq=select+C+where+A+=+'{ctx.author_id}'"
            ) as r:
                results = json.loads((await r.text()).lstrip(")]}'"))
            async with cs.get(
                    "https://docs.google.com/spreadsheets/d/"
                    f"14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc/gviz/tq?tq=select+C+where+A+=+'{ctx.author_id}'"
            ) as r:
                rank = json.loads((await r.text()).lstrip(")]}'"))

        try:
            """
            Snippet of example data:
            
            {
            'version': '0.6', 'reqId': '0', 'status': 'ok', 'sig': '781612439', 
            'table': {
                'cols': [
                    {
                    'id': 'C', 'label': 'Total Plat Value Donated (Est)', 
                    'type': 'number', 'pattern': '0'
                    }
                ], 
                'rows': [
                    {
                    'c': [
                        {'v': 7359.0, 'f': '7359'}
                        ]
                    }
                ], 
                'parsedNumHeaders': 0
                }
            }
            
            Can't understand it? Me neither.
            """
            # yeah the table's kinda funky, what're you gonna do about it
            plat = results['table']['rows'][0]['c'][0]['f']

            # TODO: "x plat to next title" (hidden if at highest rank)
            title = "**Plat required for next title**"

            # TODO: ranking in server (with proper englishesque parser)
            rank = "" if help else "a"

            message = [
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
        except IndexError:
            await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?")

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
