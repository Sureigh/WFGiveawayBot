# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash
import discord
import aiosqlite

import config

DATABASE_NAME = "configs.db"


class Config(commands.Cog):
    """Manages the ASQLite database system and helps fetch/store data when needed"""

    def __init__(self, bot):
        self.bot = bot
        bot.db = DATABASE_NAME

        # You feed it the context and tell you what value you want, it gives you the value back. Simple, right?
        async def fetch(ctx, value):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                # Yes, I know I could use ? instead.
                # Yes, I tried it.
                # No, it doesn't work for some reason. Just... let this snippet stay as it is.
                cursor = await db.execute(f"""
                    SELECT {value} FROM config
                    WHERE guild = {ctx.guild_id};
                """)
                result = await cursor.fetchone()

                # If entry is missing/broken/whatever - create a new one from scratch
                if result is None:
                    await db.execute("""
                        INSERT INTO config (guild)
                        VALUES (?);
                    """, (ctx.guild_id,))
                    await db.commit()
                    result = await fetch(ctx, value)

            return result[0]

        # Fetch color of embed
        async def color(ctx):
            return discord.Color(int(await fetch(ctx, "embed_colors"), base=16))

        # Fetch message evocation visibility
        async def hidden(ctx):
            return bool(await fetch(ctx, "hide_command_evocation"))

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
                cursor = await db.execute("""
                    SELECT plat, rank, title FROM sheet
                    WHERE user = ?;
                """, (ctx.author_id,))
                return await cursor.fetchone()

        # Checks if a user is disqualified or not on the current server
        async def disq(user):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                cursor = await db.execute("""
                    SELECT duration FROM disq
                    WHERE user = ? AND guild = ?;
                """, (user.id, user.guild.id))
                return bool(await cursor.fetchone())

        # Makes all of the previous fetches available as attribute
        # Oh yeah, this is big brain time.
        for k, v in {f.__name__: f for f in [color, hidden, rank, debug, ranks, value, disq]}.items():
            setattr(bot, k, v)

        # Builds tables.
        # I swear I'm high as fuck
        async def async_init():
            async with aiosqlite.connect(DATABASE_NAME) as db:
                # The ); at the end of each query is meant to show how I feel about SQL queries
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        guild INTEGER NOT NULL PRIMARY KEY,
                        embed_colors TEXT DEFAULT '2c2f33',
                        hide_command_evocation INTEGER DEFAULT 1,
                        rank_equal_to_threshold INTEGER DEFAULT 1,
                        debug_mode INTEGER DEFAULT 0,
                        disq_role INTEGER
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS cmds (
                        name NOT NULL,
                        resp TEXT,
                        user INTEGER,
                        cmd_id INTEGER
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS giveaways (
                        guild INTEGER NOT NULL PRIMARY KEY,
                        message INTEGER, 
                        end TIMESTAMP
                    );
                """)
                # THIS TOOK ME AN HOUR TO WRITE SOMEONE BETTER APPRECIATE THIS OR I'M GONNA BE REALLY ANGRY
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS ranks (
                        guild INTEGER NOT NULL PRIMARY KEY,
                        rank_name TEXT,
                        rank_threshold INTEGER,
                        UNIQUE(guild, rank_name),       -- Unique rank threshold per guild
                        UNIQUE(guild, rank_threshold)   -- Unique rank name per guild
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS disq (
                        guild INTEGER,
                        user INTEGER, 
                        duration TIMESTAMP
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

        bot.loop.create_task(async_init())

    @slash.cog_slash(name="config", description="Edit command configurations for the bot.",
                     guild_ids=config.guilds)
    async def config(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Config(bot))
