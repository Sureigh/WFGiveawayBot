# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Config(commands.Cog):
    """Manages the ASQLite database system and helps fetch/store data when needed"""

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Config(bot))
