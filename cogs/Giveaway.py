# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Giveaway(commands.Cog):
    """
    The actual cog that adds in giveaway-related commands,
    and creates timers so the bot can actually declare winners.
    """

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Giveaway(bot))
