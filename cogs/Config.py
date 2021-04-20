# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import aiosqlite

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

        async def color(ctx):
            return discord.Color(int(await fetch(ctx, "embed_colors"), base=16))

        async def hidden(ctx):
            return bool(await fetch(ctx, "hide_command_evocation"))

        async def rank(ctx):
            return bool(await fetch(ctx, "rank_equal_to_threshold"))

        async def debug(ctx):
            return bool(await fetch(ctx, "debug_mode"))

        async def ranks(ctx):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                cursor = await db.execute("""
                    SELECT * FROM ranks
                    WHERE guild = ?;
                """, (ctx.guild_id,))
                return await cursor.fetchall()

        async def value(ctx):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM sheet
                    WHERE user = ?;
                """, (ctx.author_id,))
                return await cursor.fetchone()

        bot.color = color
        bot.hidden = hidden
        bot.rank = rank
        bot.debug = debug
        bot.ranks = ranks
        bot.value = value

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
                        debug_mode INTEGER DEFAULT 0
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
                    CREATE TABLE IF NOT EXISTS sheet (
                        user INTEGER NOT NULL PRIMARY KEY ON CONFLICT REPLACE,
                        plat INTEGER,
                        rank INTEGER,
                        title TEXT
                    );
                """)

        bot.loop.create_task(async_init())


def setup(bot):
    bot.add_cog(Config(bot))
