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
                cursor = await db.execute(q)
                return await cursor.fetchone()

        bot.db = query

        # I swear I'm high as fuck

        async def async_init():
            async def parse_var(q, var):
                return await bot.db("""
                    SELECT ? FROM config
                    WHERE guild = ?
                """, (var, q.guild_id,))

            bot.hidden = parse_var()
            bot.color = lambda x: await bot.db("""
                SELECT hide_command_evocation FROM config
                WHERE guild = ?
            """, (x.guild_id,))

            async with aiosqlite.connect('configs.db') as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        guild INTEGER PRIMARY KEY,
                        hide_command_evocation INTEGER DEFAULT 1,
                        embed_colors TEXT DEFAULT #2C2F33,
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
