# -*- coding: utf-8 -*-
import datetime  # More like, datetorture
import pickle
import re

import discord
from discord.ext import commands
from discord_slash import cog_ext as slash

import config


class GiveawayEntry(discord.Embed):
    """Each instance is supposed to represent a giveaway entry in a server."""

    def __init__(self, ctx, giveaway_data, **kwargs):
        super().__init__(**kwargs)

        def date_parser(date: str) -> datetime.datetime:
            """
            Parses and converts a string dateform into a (future) python datetime object.
            Format should follow as (number)(time unit) - e.g 3d, 2 weeks, 3w 30 seconds are all valid examples.

            (Thank you ava :verycool:)
            """

            units = dict.fromkeys('mo w d m s'.split(), 0)
            for length, unit in re.findall(r"(\d+)\s*?(mo|[wdms])", date, flags=re.I):
                units[unit.lower()] += int(length)
            month, week, day, minute, second = units.values()
            week += month * 4.345  # haha yes no month signifiers in timedelta
            return datetime.datetime.now() + datetime.timedelta(weeks=week, days=day, minutes=minute, seconds=second)

        def giveaway_parser(giveaway_data: str) -> dict:
            """
            giveaway_data should be written like the following split into rows:
            Date, Platform data w/ giveaway row (Optional), [This can be split into two rows, too]
            Item name,
            Restrictions (Either custom or keywords will be searched),
            Donators,
            Description (Optional)

            Example data:
            4d PC | R3186
            5k Platinum
            Restrictions: 400-1000 in game hours, Less than 1500 plat balance, 2.5 Mil credits for the trade tax.
            Donated By: SomeUser#1234
            Contact OtherUser#3456 for Pickup

            Raw data returned should be:
                - Date
                - Platform
                - Row (merged with above into author heading)
                - Restrictions
                - Donor
                - Sender
                - Description
            """
            # TODO: Replace anything starting with config_ and put in bot config
            data = {}
            platform = row = None
            config_row_signifier = "R"
            config_platforms = ["PC", "Xbox", "Switch", "PS4"]
            config_keywords = ["donate", "pickup", "contact"]

            # TODO: C'mon, Sera. There has to be a better way than this, right?
            for line in giveaway_data.splitlines():
                # Date
                if data.get("time") is None and line[0].isdigit():
                    # If date_parser successfully detected a valid timestamp
                    if not datetime.datetime.now() >= (time := date_parser(line)):
                        data["time"] = time

                # Platform
                # TODO: add platforms config

                elif (data.get("platform") is None and
                      (match := re.search(rf"(?:^|\s)({'|'.join(config_platforms)})", line, flags=re.I))):
                    platform = {p.lower(): p for p in config_platforms}[match[0].lower()]

                # Restrictions
                # TODO: Something something config
                elif data.get("restriction") is None and (match := re.search("restrict", line, flags=re.I)):
                    pass

                # Donor/Sender
                # TODO: maybe add these key words in config too? just to let staff know "hey we searchin these"
                elif match := re.search(rf"((?P<type>{'|'.join(config_keywords)}).*?(?P<user>\w+#\d+))",
                                        line, flags=re.I):
                    pass

                # Anything else that doesn't match will be added to the description.
                else:
                    if data.get("description") is None:
                        pass

            data["platform_row"] = platform + row

        self.data = giveaway_parser(giveaway_data)

        # self.timestamp

        # TODO: Process giveawa_data
        # TODO: Setup giveaway

    def __conform__(self, protocol):
        """Adapts giveaway data so that it may be safely stored by the sqlite database."""
        return pickle.dumps(self)

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
        """
        Should look like:
        User's disqualification history:
            - start-end
            - start-end
            - start-end
        or
        <User has not been disqualified on this server yet.>
        """
        if not self.bot.disq(user):
            return await ctx.send("User has not been disqualified on this server yet.")

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
    async def give_start(self, ctx, giveaway_data, channel: discord.TextChannel = None):
        """
        Starts a giveaway on a given channel.

        giveaway_data should be written like the following, split into rows:
        Platform data w/ giveaway row (Optional),
        Item name,
        Restrictions (Either custom or keywords will be searched),
        Description (Optional)
        """

        async def giveaway():
            return GiveawayEntry(ctx, giveaway_data)

        giveaway = await self.bot.loop.run_in_executor(None, giveaway)

        # TODO: insert (and convert) GiveawayEntry into SQLiteDB
        # TODO: Make this part of config, I guess?
        config_msg = "__ :tada: Giveaway :tada: __"

        if channel is None:
            return await ctx.send(config_msg, embed=giveaway)
        await channel.send(config_msg, embed=giveaway)

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
