# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Error(commands.Cog):
    """
    Handles command/bot-related errors and adds a few custom ones,
    so we can return a custom message for every different error
    """

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Error(bot))
