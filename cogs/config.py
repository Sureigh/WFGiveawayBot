# -*- coding: utf-8 -*-

import pickle
from sqlite3 import PARSE_DECLTYPES

import aiosqlite
import discord
from discord.ext import commands

from configs import DATABASE_NAME


class Config(commands.Cog):
    """Manages the ASQLite database system and helps fetch/store data when needed"""

    def __init__(self, bot):
        self.bot = bot

        # Custom objects
        aiosqlite.register_converter("GIVEAWAY", lambda x: pickle.loads(x))
        aiosqlite.register_converter("COMMAND", lambda x: pickle.loads(x))

        # You feed it the context and tell you what value you want, it gives you the value back. Simple, right?
        async def fetch(ctx, _value):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                # Yes, I know I could use ? instead.
                # Yes, I tried it.
                # No, it doesn't work for some reason. Just... let this snippet stay as it is.
                # P.S: Fuck you, Lyric
                async with db.execute(f"""
                    SELECT {_value} FROM config
                    WHERE guild = {ctx.guild.id};
                """) as cursor:
                    result = await cursor.fetchone()

                # If entry is missing/broken/whatever - create a new one from scratch
                if result is None:
                    await db.execute("""
                        INSERT INTO config (guild)
                        VALUES (?);
                    """, (ctx.guild.id,))
                    await db.commit()
                    result = await fetch(ctx, _value)

            return result[0]

        # Fetch color of embed
        async def color(ctx):
            return discord.Color(int(await fetch(ctx, "embed_colors"), base=16))

        # Rank equal to threshold
        async def rank(ctx):
            return bool(await fetch(ctx, "rank_equal_to_threshold"))

        # Debug mode
        async def debug(ctx):
            return bool(await fetch(ctx, "debug_mode"))

        # Checks for custom plat threshold value
        async def ranks(ctx):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                cursor = await db.execute("""
                    SELECT * FROM ranks
                    WHERE guild = ?;
                """, (ctx.guild_id,))
                return await cursor.fetchall()

        # Fetches plat, title and ranking on spreadsheet
        async def value(ctx):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT plat, rank, title FROM sheet
                    WHERE user = ?;
                """, (ctx.author_id,)) as cursor:
                    return cursor.fetchone()

        # Checks if a user is disqualified or not on the current server
        async def disq(user):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                async with await db.execute("""
                    SELECT duration FROM disq
                    WHERE user = ? AND guild = ?;
                """, (user.id, user.guild.id)) as cursor:
                    return bool(await cursor.fetchone())

        # Makes all of the previous fetches available as attribute
        # Oh yeah, this is big brain time.
        for f in [color, rank, debug, ranks, value, disq]:
            setattr(bot, f.__name__, f)

        # Builds tables.
        # I swear I'm high as fuck
        async def async_init():
            async with aiosqlite.connect(DATABASE_NAME, detect_types=PARSE_DECLTYPES) as db:
                # The ); at the end of each query is meant to show how I feel about SQL queries
                # TODO: Each entry could also be a config object! hehe
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        guild INTEGER NOT NULL PRIMARY KEY,
                        embed_colors TEXT DEFAULT '2c2f33',
                        hide_command_evocation INTEGER DEFAULT 1,
                        rank_equal_to_threshold INTEGER DEFAULT 1,
                        debug_mode INTEGER DEFAULT 0,
                        disq_role INTEGER,
                        giveaway_role INTEGER
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS cmds (
                        guild INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        owner INTEGER NOT NULL,
                        cmd COMMAND NOT NULL
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS giveaways (
                        guild INTEGER NOT NULL,
                        giveaway GIVEAWAY NOT NULL,
                        g_end REAL NOT NULL,
                        g_id TEXT,
                        ended INTEGER DEFAULT 0
                    );
                """)
                # THIS TOOK ME AN HOUR TO WRITE SOMEONE BETTER APPRECIATE THIS OR I'M GONNA BE REALLY ANGRY
                # TODO: Maybe a rank could be a Rank object?
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS ranks (
                        guild INTEGER NOT NULL,
                        rank_name TEXT,
                        rank_threshold INTEGER,
                        UNIQUE(guild, rank_name),       -- Unique rank threshold per guild
                        UNIQUE(guild, rank_threshold)   -- Unique rank name per guild
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS disq (
                        guild INTEGER NOT NULL,
                        user INTEGER NOT NULL,
                        disq_start REAL NOT NULL,
                        disq_end REAL NOT NULL,
                        reason TEXT
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS sheet (
                        user INTEGER NOT NULL PRIMARY KEY,
                        plat INTEGER,
                        rank INTEGER,
                        title TEXT
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS prefixes (
                        guild INTEGER NOT NULL,
                        prefix TEXT NOT NULL DEFAULT "g?"
                    );
                """)
                await db.commit()
        bot.loop.create_task(async_init())

    @commands.command(name="config", description="Edit command configurations for the bot.")
    @commands.has_guild_permissions(manage_messages=True)
    async def config(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Config(bot))
