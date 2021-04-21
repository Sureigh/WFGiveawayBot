# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash
import discord


class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

    # TODO: Make guild_ids sync with internal config system
    @slash.cog_slash(name="plat", description="Check how much plat you've donated to the server.",
                     guild_ids=[465910450819694592, 487093399741267968])
    async def plat_count(self, ctx):
        bot = ctx.bot
        hidden = False
        await ctx.defer(hidden)

        # Fails if the user ID is not on the sheet
        # YES I'M USING WALRUSES WHAT DO YOU WANT GO AWAY
        if (row := await bot.value(ctx)) is None:
            await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?", hidden=hidden)
            return

        row = {k: v for k, v in zip(row.keys(), row)}

        def parse_ordinal(num):
            # Thanks Olivia uwu
            ordinal = {1: f"{num}st", 2: f"{num}nd", 3: f"{num}rd"}
            if num in [11, 12, 13] or (place := ordinal.get(num % 10)) is None:
                return f"{num}th"
            return place

        def parse_title(title):
            if title is not None:
                return ["**Current donator rank:**", f"{title}\n"]
            return ""

        message = [
            "**__Your donation statistics:__**",
            "**Total donated platinum:**",
            f"{row['plat']} platinum\n",
            *parse_title(row['title']),
            f"{parse_ordinal(row['rank'])} place in leaderboard"
        ]

        if not hidden:
            # This makes me want to drink hand sanitizer
            embed = discord.Embed(title=message[0],
                                  color=await bot.color(ctx))
            embed.add_field(name=message[1], value=message[2], inline=False)
            if message[3] != "":
                embed.add_field(name=message[3], value=message[4])
            embed.set_footer(text=message[-1])
            await ctx.send(embed=embed)
        else:
            await ctx.send("\n".join(message), hidden=hidden)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # reaction should be the tada emote, duh
        # the reaction should also be added on a valid giveaway

        # if all(reaction == "the tada emote idk", ):
        pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
