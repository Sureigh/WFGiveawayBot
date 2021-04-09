#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from discord.ext import commands
import config

# !! IMPORTANT !!
# Load Error first every time; It has custom errors that other cogs depend on, and handles errors too
COGS = ["Error", "Config", "Giveaway"]

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        # TODO: when_mentioned_or also takes function references,
        #  (I think? You should probably check that too)
        #  so replace static prefix with by-server
        super().__init__(command_prefix=commands.when_mentioned_or('$'), **kwargs)
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
    bot.run(config.TOKEN)
