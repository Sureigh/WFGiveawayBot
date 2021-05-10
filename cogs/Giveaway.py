# -*- coding: utf-8 -*-
import datetime  # More like, datetorture
import re

import discord
from discord.ext import commands
from discord_slash import cog_ext as slash

import config

class GiveawayEntry:
    """Each instance is supposed to represent a giveaway entry in a server."""

    # TODO: Add class method to edit giveaway timer
    def __init__(self, ctx, giveaway_data, duration):
        def date_parser(date: str) -> datetime.datetime:
            """
            Parses and converts a string dateform into a (future) python datetime object.
            Format should follow as (number)(time unit) - e.g 3d, 2 weeks, 3w 30 seconds are all valid examples.

            (Thank you ava :verycool:)
            """

            units = dict.fromkeys('mo w d m s'.split(), 0)
            for length, unit in re.findall(r"(\d+)\s*(mo|[wdms])", date, flags=re.I):
                units[unit.lower()] += int(length)
            month, week, day, minute, second = units.values()
            week += month * 4.345  # haha yes no month signifiers in timedelta
            return datetime.datetime.now() + datetime.timedelta(weeks=week, days=day, minutes=minute, seconds=second)

        self.date = date_parser
        self.duration = date_parser(duration)

        # TODO: Process giveawa_data
        # TODO: Setup giveaway

        self.embed = discord.Embed(title=".")

    def __conform__(self, protocol):
        """Adapts giveaway data so that it may be safely stored by the sqlite database."""
        # TODO
        pass

    def edit(self, **kwargs):
        """Edits the giveaway's information."""
        # TODO
        pass

# TODO: fun fact checks (might) be fucked, find out if they actually are lmao
class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    # Thanks Olivia uwu
    def parse_ordinal(num):
        ordinal = {1: f"{num}st", 2: f"{num}nd", 3: f"{num}rd"}
        if num in [11, 12, 13] or (place := ordinal.get(num % 10)) is None:
            return f"{num}th"
        return place

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

        embed = discord.Embed(title="**__Your donation statistics:__**", color=await bot.color(ctx))
        embed.add_field(name="**Total donated platinum:**", value=f"{row['plat']} platinum", inline=False)
        if row['title'] is not None:
            embed.add_field(name="**Current donator rank:**", value=f"{row['title']}")
        embed.set_footer(text=f"{self.parse_ordinal(row['rank'])} place in leaderboard")

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

    @slash.cog_subcommand(base="disqualify", name="check", description="Check a user's disqualification history.",
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
                          description="Check how long until you or a user is re-eligible for giveaways.",
                          guild_ids=config.guilds)
    async def disq_time(self, ctx, user: discord.Member = None):
        # This should return a timedelta? iunno lol
        if user is None:
            ctx.bot.disq(ctx.author)
        ctx.bot.disq(user)

    @slash.cog_subcommand(base="giveaway", name="start", description="Start a new giveaway. (See help for more info)",
                          guild_ids=config.guilds)
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), commands.has_any_role())
    async def give_start(self, ctx, giveaway_data, duration, channel: discord.TextChannel = None):
        """
        Starts a giveaway on a given channel.

        giveaway_data should be written like the following, split into rows:
        Platform data w/ giveaway row (Optional)
        Item name
        Restrictions (Either custom or keywords will be searched)
        Description (Optional)
        """
        giveaway = GiveawayEntry(ctx, giveaway_data, duration)
        # TODO: insert (and convert) GiveawayEntry into SQLiteDB

        if channel is None:
            return await ctx.send(embed=giveaway.embed)
        await channel.send(embed=giveaway.embed)

    @slash.cog_subcommand(base="giveaway", name="reroll", description="Reroll a finished giveaway.",
                          guild_ids=config.guilds)
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), commands.has_any_role())
    async def give_reroll(self, ctx, giveaway_id: int):
        pass

    @slash.cog_subcommand(base="giveaway", name="end", description="End an existing giveaway.", guild_ids=config.guilds)
    async def give_end(self, ctx, giveaway_id: int):
        pass

    @slash.cog_subcommand(base="giveaway", name="edit",
                          description="Edit an existing giveaway's duration or restriction(s).",
                          guild_ids=config.guilds, )
    async def give_edit(self, ctx, giveaway_id: int):
        pass

    # TODO: print a copy of the ongoing giveaway, with labels on each part of the giveaway, then ask for what to edit

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
