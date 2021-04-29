#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from discord_slash import SlashCommand
from discord.ext import commands
import discord
import config

# !! IMPORTANT !!
# Load Error first every time; It has custom errors that other cogs depend on, and handles errors too
# TODO: so where them custom errors at homie
COGS = ["Error", "Config", "General", "Giveaway", "Sheet", "Timers"]


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, **kwargs)

        # SLASH COMMANDS
        # DISGUSTING
        SlashCommand(self, override_type=True, sync_commands=True)

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
    bot.run(config.TOKEN)
