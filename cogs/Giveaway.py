# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash
import discord

import config

class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

    # TODO: Make guild_ids sync with internal config system
    @slash.cog_slash(name="plat", description="Check how much plat you've donated to the server.",
                     guild_ids=config.guilds)
    async def plat_count(self, ctx):
        bot = ctx.bot
        hidden = False
        await ctx.defer(hidden)

        # Fails if the user ID is not on the sheet
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

        if not hidden:
            embed = discord.Embed(title="**__Your donation statistics:__**",
                                  color=await bot.color(ctx))
            embed.add_field(name="**Total donated platinum:**", value=f"{row['plat']} platinum", inline=False)
            if row['title'] is not None:
                embed.add_field(name="**Current donator rank:**", value=f"{row['title']}")
            embed.set_footer(text=f"{parse_ordinal(row['rank'])} place in leaderboard")

            await ctx.send(embed=embed)
        else:
            message = [
                "**__Your donation statistics:__**",
                "**Total donated platinum:**",
                f"{row['plat']} platinum\n",
                f"**Current donator rank:**:\n{row['title']}\n" if row['title'] is not None else "",
                f"{parse_ordinal(row['rank'])} place in leaderboard"
            ]

            await ctx.send("\n".join(message), hidden=hidden)

    @slash.cog_slash(name="donation", description="Fill out a donation form to donate your items.",
                     guild_ids=config.guilds)
    async def donation(self, ctx):
        pass

    @slash.cog_subcommand(base="disqualify", name="user", description="Disqualify a user.",
                          guild_ids=config.guilds)
    async def disq_user(self, ctx, user: discord.Member, duration):
        pass

    @slash.cog_subcommand(base="disqualify", name="time",
                          description="Check how long until you're re-eligible for giveaways.",
                          guild_ids=config.guilds)
    async def disq_time(self, ctx):
        # This should return a timedelta? iunno lol
        ctx.bot.disq(ctx.author)

    @slash.cog_subcommand(base="disqualify", name="check", description="Check a user's disqualification history",
                          guild_ids=config.guilds)
    async def disq_check(self, ctx, user: discord.Member):
        if not self.bot.disq(user):
            return await ctx.send("User has not been disqualified on this server yet.")
        # Should look like:
        """
        User's disqualification history:
            - start-end
            - start-end
            - start-end
        or 
        <User has not been disqualified on this server yet.>
        """

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # reaction should be the tada emote, duh
        # the reaction should also be added on a valid giveaway

        # if all(reaction == "the tada emote idk", ):

        # if user is not eligible and re-reacts to it multiple times (configurable amount), they get auto disq
        pass

    # Handles dodging of disqualification
    @commands.Cog.listener()
    async def on_member_leave(self, member):
        # TODO: Start a timer, to create a time delta
        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if self.bot.disq(member):
            # TODO: Add time delta to remaining duration (Add config option for extra disq dur as punishment)
            pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
