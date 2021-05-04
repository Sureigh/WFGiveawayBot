# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash
import discord

import datetime  # More like, datetorture
import re

import config


# TODO: fun fact checks (might) be fucked, find out if they actually are lmao
class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

        def date_parser(date: str) -> datetime.timedelta:
            """
            Parses and converts a string dateform into a python timedelta object.
            Format should follow as (number)(time unit) - e.g 3d, 2 weeks, 3w 30 seconds are all valid examples.
            """
            # TODO: oh god i didn't think abou what to do with how to sort and parse this data as a timedelta FUCK
            times = [time.lowercase() for time in re.findall(r"(\d+\s*(?:mo|[wdms]))", date, flags=re.I)]
            order = {k: i for i, k in enumerate(("mo", "w", "d", "m", "s"))}
            times = sorted(times, key=lambda t: order[re.search(r"mo|[wdms]", t)[0]])

            return datetime.timedelta()

    # TODO: Make guild_ids sync with internal config system
    @slash.cog_slash(name="plat", description="Check how much plat you've donated to the server.",
                     guild_ids=config.guilds)
    async def plat_count(self, ctx):
        bot = ctx.bot
        hidden = await bot.hidden(ctx)
        await ctx.defer(hidden)

        # Fails if the user ID is not on the sheet
        if (row := await bot.value(ctx)) is None:
            await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?", hidden=hidden)
            return

        row = {k: v for k, v in zip(row.keys(), row)}

        # Thanks Olivia uwu
        def parse_ordinal(num):
            ordinal = {1: f"{num}st", 2: f"{num}nd", 3: f"{num}rd"}
            if num in [11, 12, 13] or (place := ordinal.get(num % 10)) is None:
                return f"{num}th"
            return place

        embed = discord.Embed(title="**__Your donation statistics:__**", color=await bot.color(ctx))
        embed.add_field(name="**Total donated platinum:**", value=f"{row['plat']} platinum", inline=False)
        if row['title'] is not None:
            embed.add_field(name="**Current donator rank:**", value=f"{row['title']}")
        embed.set_footer(text=f"{parse_ordinal(row['rank'])} place in leaderboard")

        await ctx.send(embed=embed, hidden=hidden)

    @slash.cog_slash(name="donation", description="Fill out a donation form to donate your items.",
                     guild_ids=config.guilds)
    async def donation(self, ctx):
        pass

    @slash.cog_subcommand(base="disqualify", name="user", description="Disqualify a user from joining giveaways.",
                          guild_ids=config.guilds)
    @commands.has_guild_permissions(manage_messages=True)
    async def disq_user(self, ctx, user: discord.Member, duration, reason=None):
        pass

    @slash.cog_subcommand(base="disqualify", name="check", description="Check a user's disqualification history",
                          guild_ids=config.guilds)
    @commands.has_guild_permissions(manage_messages=True)
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

    @slash.cog_subcommand(base="disqualify", name="time",
                          description="Check how long until you're re-eligible for giveaways.",
                          guild_ids=config.guilds)
    async def disq_time(self, ctx):
        # This should return a timedelta? iunno lol
        ctx.bot.disq(ctx.author)

    @slash.cog_subcommand(base="giveaway", name="start", description="Start a new giveaway.", guild_ids=config.guilds)
    @commands.has_any_role()  # TODO: Moderator or giveaway role
    async def give_start(self, ctx, duration, item, ):
        # TODO: How're you gonna parse the time? Figure it out.
        pass

    @slash.cog_subcommand(base="giveaway", name="end", description="End an existing giveaway.", guild_ids=config.guilds)
    async def give_end(self, ctx, giveaway_id: int):
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
