# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import aiohttp
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
        await ctx.defer(hidden=await bot.hidden(ctx))

        async with aiohttp.ClientSession(headers={"X-DataSource-Auth": "true"}) as cs:
            async with cs.get(
                "https://docs.google.com/spreadsheets/d/"
                f"14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc/gviz/tq?tq=select+C+where+A+=+'{ctx.author_id}'"
            ) as r:
                results = json.loads((await r.text()).lstrip(")]}'"))
                try:
                    plat = results['table']['rows'][0]['c'][0]['f']
                    # TODO: a "how much plat to next title" counter sorta
                    embed = discord.Embed(title="__Plat count__", description=plat,
                                          color=await bot.color(ctx))
                    await ctx.send(embed=embed)
                # Fails if the user ID is not on the sheet
                except IndexError:
                    await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?")

    @slash.cog_slash(name="test", guild_ids=[465910450819694592])
    async def test(self, ctx, pee):
        await ctx.send(pee + " this was a test command bro")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # reaction should be the tada emote, duh
        # the reaction should also be added on a valid giveaway
        # if all(reaction == "the tada emote idk", ):
        pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
