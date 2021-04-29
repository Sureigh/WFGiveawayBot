# -*- coding: utf-8 -*-

from discord.ext import commands

class Error(commands.Cog):
    """
    Handles command/bot-related errors and adds a few custom ones,
    so we can return a custom message for every different error
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if await ctx.bot.debug(ctx):
            await ctx.channel.send(f"{error.__class__.__name__}: {error}")

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, error):
        if await ctx.bot.debug(ctx):
            await ctx.channel.send(f"{error.__class__.__name__}: {error}")

def setup(bot):
    bot.add_cog(Error(bot))
