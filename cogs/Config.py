# -*- coding: utf-8 -*-

from discord.ext import commands, tasks
import discord
import aiosqlite
from typing import Union, Tuple


class Config(commands.Cog):
    """Manages the ASQLite database system and helps fetch/store data when needed"""

    def __init__(self, bot):
        self.bot = bot

        # Only meant for SELECT queries
        async def query(*q):
            async with aiosqlite.connect('configs.db') as db:
                cursor = await db.execute(*q)
                return await cursor.fetchone()

        async def fetch(ctx, value):
            return await bot.query("""
                SELECT ? FROM config
                WHERE guild = ?
            """, (value, ctx.guild_id))

        async def hidden(ctx):
            return bool(await fetch(ctx, "hide_command_evocation"))

        async def color(ctx):
            return discord.Color(hex(int(*await fetch(ctx, "embed_colors"), base=16)))

        bot.query = query
        bot.hidden = hidden
        bot.color = color

        # I swear I'm high as fuck
        async def async_init():
            async with aiosqlite.connect('configs.db') as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        guild INTEGER PRIMARY KEY,
                        hide_command_evocation INTEGER DEFAULT 1,
                        embed_colors TEXT DEFAULT "2c2f33",
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
