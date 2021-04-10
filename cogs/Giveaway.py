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

    @slash.cog_slash(name="platcount")
    async def platcount(self, ctx):
        async with aiohttp.ClientSession(headers={"X-DataSource-Auth": "true"}) as cs:
            async with cs.get(
                "https://docs.google.com/spreadsheets/d/"
                f"14t9-54udr_eqaCgq9g1rWhPLHY_E-RxfdhKTXxgCERc/gviz/tq?tq=select+C+where+A+=+'{ctx.author_id}'"
            ) as r:
                # TODO: Send this in a nice clean embed ig
                results = json.loads((await r.text()).lstrip(")]}'"))
                plat = results['table']['rows'][0]['c'][0]['f']
                await ctx.send()

def setup(bot):
    bot.add_cog(Giveaway(bot))
