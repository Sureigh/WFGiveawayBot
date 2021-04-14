# -*- coding: utf-8 -*-

from discord.ext import commands
import discord
import aiosqlite

DATABASE_NAME = "configs.db"


class Config(commands.Cog):
    """Manages the ASQLite database system and helps fetch/store data when needed"""

    def __init__(self, bot):
        self.bot = bot

        # You feed it the context and tell you what value you want, it gives you the value back. Simple, right?
        async def fetch(ctx, value):
            async with aiosqlite.connect(DATABASE_NAME) as db:
                # Yes, I know I could use ? instead.
                # Yes, I tried it.
                # No, it doesn't work for some reason. Just... let this snippet stay as it is.
                cursor = await db.execute("""
                    SELECT {0} FROM config
                    WHERE guild = {1}
                """.format(value, ctx.guild_id))
                result = await cursor.fetchone()

                # If entry is missing/broken/whatever - create a new one from scratch
                if result is None:
                    await db.execute("""
                        INSERT INTO config (guild)
                        VALUES (?)
                    """, (ctx.guild_id, ))
                    await db.commit()
                    result = await fetch(ctx, value)

            return result

        async def hidden(ctx):
            return bool(await fetch(ctx, "hide_command_evocation"))

        async def color(ctx):
            return discord.Color(hex(int(await fetch(ctx, "embed_colors"), base=16)))

        async def debug(ctx):
            return bool(await fetch(ctx, "debug_mode"))

        bot.hidden = hidden
        bot.color = color
        bot.debug = debug

        # I swear I'm high as fuck
        async def async_init():
            async with aiosqlite.connect(DATABASE_NAME) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        guild INTEGER PRIMARY KEY,
                        hide_command_evocation INTEGER DEFAULT 1,
                        embed_colors TEXT DEFAULT '2c2f33',
                        debug_mode INTEGER DEFAULT 0
                    );
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS giveaways (
                        guild INTEGER,
                        message INTEGER, 
                        end TIMESTAMP
                    );
                """)

        bot.loop.create_task(async_init())


def setup(bot):
    bot.add_cog(Config(bot))
