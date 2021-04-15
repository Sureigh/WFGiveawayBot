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
        hidden = await bot.hidden(ctx)
        await ctx.defer(hidden)

        async with aiohttp.ClientSession(headers={"X-DataSource-Auth": "true"}) as cs:
            async with cs.get(
                    "https://docs.google.com/spreadsheets/d/"
                    f"14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc/gviz/tq?tq=select+C+where+A+=+'{ctx.author_id}'"
            ) as r:

                # TODO: yeeeah baby crack this boy open and sip its data up mmmm yummy sorting
                results = json.loads((await r.text()).lstrip(")]}'"))
                try:
                    plat = results['table']['rows'][0]['c'][0]['f']

                    ranks = {

                    }

                    plat_str = f"{plat} platinum"
                    # TODO: "x plat to next title" (hidden if at highest rank)
                    # TODO: leaderboard showing ("you are at #x")

                    message = [
                        "Total donated platinum:",
                        plat_str,

                    ]
                    embed = discord.Embed(title=message[0], description=message[1],
                                          color=await bot.color(ctx))
                    await ctx.send(message, embed=embed, hidden=hidden)
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
