# -*- coding: utf-8 -*-
import datetime  # More like, datetorture
import pickle
import re

import discord
import discord_slash
from discord.ext import commands
from discord_slash import cog_ext as slash
import humanfriendly

import config
from Error import GiveawayError


# TODO: Big brain performance saving method:
#  Check that there are giveaways within the TIMER variable's time frame.
#  If there are, when once giveaway ends, stop that process and then start a new one that ends at timedelta!
#  Therefore we can just reuse "one" process infinitely within that timer frame
class GiveawayEntry(discord.Embed):
    """Each instance is supposed to represent a giveaway entry in a server."""

    def __init__(self, ctx: discord_slash.SlashContext, giveaway_data, **kwargs):
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

        def giveaway_parser(giveaway: str) -> dict:
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
                - Row number (merged with above into author heading)
                - Item
                - Restrictions
                - Donor
                - Sender
                - Description
            """
            # TODO: Replace anything starting with config_ and put in bot config
            _data = {}
            config_row_signifier = "R"
            config_platforms = ["PC", "Xbox", "Switch", "PS4"]
            config_keywords = {"donor": ["donor", "donate"],
                               "sender": ["sender", "pickup", "contact"]}

            # Thanks snek uwu
            def check_date(_line):
                if m := re.search(r"(\d+)\s*?(?:mo|[wdms])", _line, flags=re.I):
                    if datetime.datetime.now() < (_time := date_parser(m[1])):
                        return time

            def check_plat(_line):
                if m := re.search(rf"(?:^|\s)({'|'.join(config_platforms)})", _line, flags=re.I):
                    return {p.lower(): p for p in config_platforms}[m[1].lower()]

            def check_row(_line):
                if m := re.search(rf"(?<!\w){config_row_signifier}\d+", _line, flags=re.I):
                    return m[0]

            def check_resc(_line):
                if m := re.search(r"restrict[\w\s]*[\s:-]*(.+)", _line, flags=re.I):
                    return m[1].strip().split(",")

            def check_donor(_line):
                if m := re.search(rf"((?:{'|'.join(config_keywords['donor'])}).*?(\w+#\d+))", _line, flags=re.I):
                    return m[1]

            def check_sender(_line):
                if m := re.search(rf"((?:{'|'.join(config_keywords['sender'])}).*?(\w+#\d+))", _line, flags=re.I):
                    return m[1]

            def check_desc(_line):
                if m := re.search(rf"desc[\w\s]*[\s:-]*(.+)", _line, flags=re.I):
                    return m[1].strip()

            checks = {
                'date': check_date,
                'plat': check_plat,
                'row': check_row,
                'resc': check_resc,
                'donor': check_donor,
                'sender': check_sender,
                'desc': check_desc
            }
            ignored = []

            for line in giveaway.splitlines():
                line.strip()
                checked = False

                for key, check in checks.items():
                    if key not in ignored and (result := check(line)):
                        _data[key] = result
                        checked = True
                        ignored.append(key)

                if not (_data.get("item") or checked):  # Item
                    _data["item"] = line

            _data["platform_row"] = _data.pop("platform", "") + _data.pop("row", "")

            return _data

        self.data = giveaway_parser(giveaway_data)
        data = self.data

        if not (time := self.data.get("date")):
            raise GiveawayError("Missing date data!")
        elif not (item := self.data.get("item")):
            raise GiveawayError("Misisng item data!")

        # Constructs the actual embed
        self.title = item
        self.timestamp = time
        self.description = "React with :tada: to join the giveaway!"
        self.set_author(name=data["platform_row"])
        if resc := self.data.get("resc"):
            self.add_field(name="Restrictions:", value="\n".join(f"- {r}" for r in resc))
        if donor := self.data.get("donor"):
            self.add_field(name="Donator:", value=donor)
        self.add_field(name="Hosted by:", value=ctx.author.mention, inline=False)

        time_left: datetime.timedelta = time - datetime.datetime.now()
        self.add_field(name="Time remaining:", value=humanfriendly.format_timespan(time_left))

        # If the time remaining for giveaway is lesser than the timer's next interval
        if time_left < datetime.timedelta(minutes=config.TIMER):
            pass
            # TODO: Add giveaway to end of giveaway queue
            #  if the time is shorter than that, however, just run it as its own task
        # If not (which should be most cases) it will shelve the giveaway on the SQL db
        else:
            pass

    def __conform__(self, protocol):
        """Adapts giveaway data so that it may be safely stored by the sqlite database."""
        return pickle.dumps(self)

    def edit(self, **kwargs):
        """Edits the giveaway's information."""
        # TODO
        pass


# TODO: fun fact checks (might) be fucked, find out if they actually are lmao
# TODO: Maybe a "giveaways won" stat? See how many they've joined is... impossible to keep track of without counting,
#  but I think one of the GSheets has winner data...
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
