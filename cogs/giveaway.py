# -*- coding: utf-8 -*-
import datetime  # More like, datetorture
import pickle
import random
import re
import typing

import aiosqlite
import discord
from discord.ext import commands
import humanfriendly

import configs
from errors import GiveawayError

# Thanks Olivia uwu
def parse_ordinal(num: int) -> str:
    ordinal = {1: f"{num}st", 2: f"{num}nd", 3: f"{num}rd"}
    if num in [11, 12, 13] or not (place := ordinal.get(num % 10)):
        return f"{num}th"
    return place


# TODO: Big brain performance saving method:
#  Check that there are giveaways within the TIMER variable's time frame.
#  If there are, when once giveaway ends, stop that process and then start a new one that ends at timedelta!
#  Therefore we can just reuse "one" process infinitely within that timer frame
class GiveawayEntry(discord.Embed):
    """Each instance is supposed to represent a giveaway entry in a server."""

    @staticmethod
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
            return datetime.datetime.utcnow() + datetime.timedelta(weeks=week, days=day, minutes=minute, seconds=second)

        # TODO: Replace anything starting with config_ and put in bot config
        _data = {}
        config_row_signifier = "R"
        config_platforms = ["PC", "Xbox", "Switch", "PS4"]
        config_keywords = {"donor": ["donor", "donate"],
                           "sender": ["sender", "pickup", "contact"]}

        # Thanks snek uwu
        def check_date(_line):
            if m := re.search(r"\d+\s*?(?:mo|[wdms])", _line, flags=re.I):
                if datetime.datetime.utcnow() < (_time := date_parser(m[0])):
                    return _time

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
            if m := re.search(rf"(?:{'|'.join(config_keywords['donor'])}).*?(\w+#\d+)", _line, flags=re.I):
                return m[1]

        def check_sender(_line):
            if m := re.search(rf"(?:{'|'.join(config_keywords['sender'])}).*?(\w+#\d+)", _line, flags=re.I):
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
            line = line.strip()
            checked = False

            for key, check in checks.items():
                if key not in ignored and (result := check(line)):
                    # print(f"Check went through with {check.__name__}, line is {line}")
                    _data[key] = result
                    checked = True
                    ignored.append(key)

            if not (_data.get("item") or checked):  # Item
                _data["item"] = line

        if (plat := _data.get('plat')) and (row := _data.get('row')):
            _data["author_header"] = f"{plat} | {row}"
        elif plat or row:
            _data["author_header"] = plat if plat else row
        else:
            _data["author_header"] = ""

        return _data

    @staticmethod
    def parse_time(t: datetime.datetime) -> str:
        """Turns a datetime object into something more human-friendly."""
        return t.strftime(f"%-I:%M %p, %a %B, {parse_ordinal(int(t.strftime('%d')))}, %Y")

    def __init__(self, ctx: commands.Context, giveaway_data, **kwargs):
        super().__init__(**kwargs)
        self.color = discord.Color.blurple()  # Old blurple best blurple
        self.data = self.giveaway_parser(giveaway_data)
        data = self.data

        if not (time := data.get("date")):
            raise GiveawayError("Missing date data!")
        elif not (item := data.get("item")):
            raise GiveawayError("Missing item data!")

        # Constructs the actual embed
        self.title = item
        self.description = f"{data.get('desc')}\n\n"
        self.set_author(name=data["author_header"])
        if resc := data.get("resc"):
            resc = "\n".join(f"- {r}" for r in resc)
        else:
            resc = "None"
        self.add_field(name="Restrictions:", value=resc, inline=False)
        if donor := data.get("donor"):
            if _ := ctx.guild.get_member_named(donor):
                donor = _.mention
            self.add_field(name="Donated by:", value=donor)
        self.add_field(name="Hosted by:", value=ctx.author.mention)

        self.set_footer(text=f"Giveaway ends at {self.parse_time(time)} UTC")

        sender = data.get('sender')
        if _ := ctx.guild.get_member_named(sender):
            sender = _.mention
        self.add_field(name=f"React with :tada: to join the giveaway!",
                       value=f"Contact user {sender} to get your items.", inline=False)

        time_left: datetime.timedelta = time - datetime.datetime.utcnow()
        self.add_field(name="Time remaining:", value=humanfriendly.format_timespan(time_left), inline=False)

        # We'll need to access these outside later :RemVV:
        self.ctx = ctx  # Original invocation context
        self.msg: discord.Message = None  # Giveaway message
        self.time = time.timestamp()  # Giveaway end time
        self.row = data.get("row")  # (Optional) row number
        self.users = 0  # Users who have joined the giveaway

        # If the time remaining for giveaway is lesser than the timer's next interval
        # If not (which should be most cases) it will shelve the giveaway on the SQL db
        if time_left < datetime.timedelta(minutes=configs.TIMER):
            pass
            # TODO: Add giveaway to end of giveaway queue
            #  if the time is shorter than that, however, just run it as its own task

    def __conform__(self, protocol):
        """Adapts giveaway data so that it may be safely stored by the sqlite database."""
        return pickle.dumps(self)

    def edit(self, **kwargs):
        """Edits the giveaway's information."""
        # TODO
        pass

    async def end(self):
        """Ends the giveaway."""
        # TODO: something something configurable emojis
        r = self.ctx.message.reactions[[str(r) for r in self.ctx.message.reactions].index(":tada:")]

        now = datetime.datetime.utcnow()
        async with aiosqlite.connect(configs.DATABASE_NAME) as db:
            # Check if disqualified
            async with await db.execute("""
                SELECT user FROM disq WHERE guild = ? AND disq_end > ?;
            """, (self.ctx.guild.id, now.timestamp())) as cursor:
                dq = [e[0] async for e in cursor]

            # Remove non eligible participants
            # TODO: Apply all possible checks here
            self.users = [u async for u in r.users() if u.id not in dq]  # Disqualified

            # Congratulate user
            # TODO: Configurable win phrases.
            config_win = ["Winner winner, chicken dinner!", "Congratulations!", "Epic victory royale moment!"
                                                                                "Wow, that's pretty poggers!",
                          "That's so cool!"]
            win = random.choice(config_win)
            user = random.choice(self.users)

            # Edit embed and handle ending
            self.set_footer(text=f"Giveaway ended at {self.parse_time(now)} UTC")
            self.add_field(name="This giveaway has ended.",
                           value=f"Final user count: {len(self.users)}", inline=False)
            self.color = discord.Color.darker_gray()
            await self.msg.edit(embed=self)

            await db.execute("UPDATE giveaways SET ended = 1 WHERE guild = ? AND g_end = ?;",
                             (self.ctx.guild.id, self.time))
            await db.commit()


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

    @commands.command(name="plat", description="Check how much plat you've donated to the server.")
    async def plat(self, ctx):
        bot = ctx.bot
        # Fails if the user ID is not on the sheet
        if (row := await bot.value(ctx)) is None:
            return await ctx.send("You haven't donated any plat yet - perhaps you can donate something today?")

        row = {k: v for k, v in zip(row.keys(), row)}

        embed = discord.Embed(title="**__Your donation statistics:__**", color=await bot.color(ctx))
        embed.add_field(name="**Total donated platinum:**", value=f"{row['plat']} platinum", inline=False)
        if row['title'] is not None:
            embed.add_field(name="**Current donator rank:**", value=f"{row['title']}")
        embed.set_footer(text=f"{parse_ordinal(row['rank'])} place in leaderboard")

        await ctx.send(embed=embed)

    @commands.command(name="donation", description="Fill out a donation form to donate your items.")
    async def donation(self, ctx):
        pass

    # Disqualify
    @commands.group(name="disqualify", aliases=["disq", "d"])
    async def disq(self, ctx):
        """All disqalification-related commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(self.disq)

    @disq.command(name="user", aliases=["u"], description="Disqualify a user from joining giveaways.")
    @commands.has_guild_permissions(manage_messages=True)
    async def disq_user(self, ctx, user: discord.Member, duration, reason=None):
        pass

    @disq.command(name="check", aliases=["c"], description="Check a user's disqualification history.")
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

    @disq.command(name="time", aliases=["t"],
                  description="Check how long until you or a user is re-eligible for giveaways.")
    async def disq_time(self, ctx, user: discord.Member = None):
        # This should return a timedelta? iunno lol
        if user is None:
            ctx.bot.disq(ctx.author)
        ctx.bot.disq(user)

    # Giveaway
    @commands.group(name="giveaway", aliases=["give", "g"])
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), commands.has_any_role())
    async def give(self, ctx):
        """All giveaway-related commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(self.give)

    @give.command(name="start", aliases=["s"])
    async def give_start(self, ctx, channel: typing.Optional[discord.TextChannel], *, giveaway_data):
        """
        Starts a giveaway on a given channel.

        giveaway_data should have the following data:
        - Ending time
        - Platform data w/ giveaway row (Optional),
        - Item name,
        - Restrictions (Either custom or keywords will be searched),
        - Description (Optional)
        """
        await ctx.trigger_typing()
        # Potentially blocking? Just in case, right?
        giveaway: GiveawayEntry = await self.bot.loop.run_in_executor(
            None, lambda: GiveawayEntry(ctx, giveaway_data)
        )

        async with aiosqlite.connect(configs.DATABASE_NAME) as db:
            c = await db.execute("SELECT * FROM giveaways WHERE guild = ? AND g_id = ?;", (ctx.guild.id, giveaway.row))
            r = await c.fetchone()
            await c.close()

            if r is not None:
                raise GiveawayError(f"Giveaway {giveaway.row} already exists!")

            # TODO: Make this part of config
            config_msg = "**__ :tada: Giveaway :tada: __**"
            if channel is None:
                msg = await ctx.send(config_msg, embed=giveaway)
            else:
                msg = await channel.send(config_msg, embed=giveaway)
            await msg.add_reaction(":tada:")
            giveaway.msg = msg

            await db.execute("INSERT INTO giveaways VALUES (?, ?, ?, ?)",
                             (ctx.guild.id, giveaway, giveaway.time, giveaway.row))
            await db.commit()

    # TODO: Although we're keeping this for archaic reasons,
    #  add in an option to be able to click a check on the finished giveaway.
    @give.command(name="reroll", aliases=["roll", "r"])
    async def give_reroll(self, ctx, giveaway_id: discord.Message):
        """Reroll the winner of a giveaway that has already ended."""
        pass

    @give.command(name="end", aliases=["e"])
    async def give_end(self, ctx, giveaway_id: discord.Message):
        """Force a giveaway to end immediately."""
        pass

    @give.command(name="edit")
    async def give_edit(self, ctx, giveaway_id: discord.Message, *, giveaway_data):
        """Edit an existing giveaway's data."""
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
