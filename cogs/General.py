# -*- coding: utf-8 -*-

from discord.ext import commands
from discord_slash import cog_ext as slash
from discord_slash.utils import manage_commands
import aiosqlite

import config


class General(commands.Cog):
    """A cog for general, uncategorized commands."""

    def __init__(self, bot):
        self.bot = bot

    # TODO: Perms check for donator/mod+
    @slash.cog_subcommand(base="command", name="create", description="Create a custom command.",
                          guild_ids=config.guilds)
    async def command_create(self, ctx, name, response, description=None):
        async with aiosqlite.connect(ctx.bot.db) as db:
            cursor = await db.execute("SELECT * FROM cmds WHERE name=?", (name,))
            if bool(await cursor.fetchone()):
                await ctx.send("A command with this name already exists. "
                               "Would you like to overwrite it instead?")
                # TODO: - invoke subcommand, then ask if yes or no to overwrite function

            # Borrowed a snippet from https://github.com/eunwoo1104/slash-bot/blob/master/main.py
            resp = await manage_commands.add_slash_command(ctx.bot.user.id, config.TOKEN,
                                                           ctx.guild_id, name, description)

            async def cmd():
                await ctx.send(response)

            await db.execute("INSERT INTO cmds VALUES (?, ?, ?, ?);",
                             (ctx.guild_id, name, ctx.author_id, resp["id"]))

        self.bot.add_slash_command(cmd, name, description, config.guilds)

    # TODO: Perms check for command creator/mod+
    @slash.cog_subcommand(base="command", name="remove", description="Remove an existing custom command.",
                          guild_ids=config.guilds)
    async def command_remove(self, ctx, name):
        self.bot.remove_slash_command(name)


def setup(bot):
    bot.add_cog(General(bot))
