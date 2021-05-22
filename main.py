#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiosqlite
import discord
from discord.ext import commands

import configs

COGS = ["error", "config", "general", "giveaway", "sheet", "timers"]


async def prefix(_bot, message):
    async with aiosqlite.connect(configs.DATABASE_NAME) as db:
        async with db.execute("SELECT prefix FROM prefixes WHERE guild = ?;", (message.guild.id,)) as c:
            _prefix = await c.fetchone()
            await c.close()

            if _prefix is None:
                await db.execute("INSERT INTO prefixes (guild) VALUES (?);", (message.guild.id,))
                await db.commit()
                return await prefix(_bot, message)

    return commands.when_mentioned_or(*_prefix)(_bot, message)

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=prefix, intents=intents, **kwargs)

        self.load_extension('jishaku')
        for cog in COGS:
            try:
                self.load_extension(f"cogs.{cog}")
                print(f"Loaded cog {cog}")
            except Exception as exc:
                print(f"Could not load extension {cog} due to {exc.__class__.__name__}: {exc}")

    async def on_ready(self):
        print("Logged on as {0} (ID: {0.id})".format(self.user))


bot = Bot()

if __name__ == "__main__":
    bot.run(configs.TOKEN)
