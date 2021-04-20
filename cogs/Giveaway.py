# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash


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
        bot = ctx.bot
        hidden = await bot.hidden(ctx)
        await ctx.defer(hidden=hidden)

        # Fails if the user ID is not on the sheet
        # YES I'M USING WALRUSES WHAT DO YOU WANT GO AWAY
        if (row := await bot.value(ctx)) is None:
            await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?")
            return

        row = {k: v for k, v in zip(row.keys(), row)}

        await ctx.send(str(row), hidden=hidden)

        """
        message = [
            "**Total donated platinum:**",
            f"{row['plat']} platinum",
            "\n",
            row['title'],
            # f"{} in leaderboard"
        ]

        embed = discord.Embed(title=message[0], description=message[1],
                              color=await bot.color(ctx))
        if hidden:
            await ctx.send("\n".join(message), hidden=hidden)
        else:
            await ctx.send(embed=embed)
        """

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # reaction should be the tada emote, duh
        # the reaction should also be added on a valid giveaway

        # if all(reaction == "the tada emote idk", ):
        pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
