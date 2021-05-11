# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
from discord.ext.commands import MissingPermissions

import io


class Error(commands.Cog):
    """
    Handles command/bot-related errors and adds a few custom ones,
    so we can return a custom message for every different error
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # if await ctx.bot.debug(ctx):
        await ctx.channel.send(f"{type(error)}: {error}")

    @commands.Cog.listener()
    async def on_slash_command_error(self, ctx, error):
        errors = {MissingPermissions: "Sorry, you must be a moderator to perform this action. 👎", }

        if e := errors.get(type(error)):
            ctx.channel.send(e)

        # if await ctx.bot.debug(ctx):
        # Does this even work? We'll find out when we get there, I guess
        if isinstance(error, discord.HTTPException):
            if error.status == 400:
                text = discord.File(io.StringIO(error.text))
                await ctx.channel.send("Your message was too long, so I've wrapped it in a file for you.", file=text)
        else:
            await ctx.channel.send(f"{error.__class__.__name__}: {error}")

def setup(bot):
    bot.add_cog(Error(bot))
