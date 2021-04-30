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
        # Permissions check
        # TODO: add this ig

        # TODO: add a configurable amount of custom commands per donator,
        #  and then check that a donator has not surpassed that amount
        if len(name) > 32:
            return await ctx.send("Command name is too long! (Over 32 characters)")

        async with aiosqlite.connect(ctx.bot.db) as db:
            # Checks if over guild command limit
            async with db.execute("SELECT * FROM cmds") as cursor:
                if len([row async for row in cursor]) >= 100:
                    return await ctx.send("Too many commands in guild! (Limit is 100 commands per guild)")

            # Checks if command already exists
            async with db.execute("SELECT * FROM cmds WHERE name=? AND guild_id=?", (name, ctx.guild_id)) as cursor:
                result = cursor.fetchone()

            if bool(result):
                if not ctx.author.guild_permissions.manage_messages:
                    return await ctx.send("A command with this name already exists.")
                else:
                    await ctx.send("A command with this name already exists.\n"
                                   "Would you like to overwrite it?\n\n**Y / N**")

                    # TODO: ask if yes or no to overwrite function

            # Borrowed a snippet from https://github.com/eunwoo1104/slash-bot/blob/master/main.py
            # Actual logic of custom commands
            option = manage_commands.create_option("Hidden", "Send reply hidden.", bool, True)

            resp = await manage_commands.add_slash_command(ctx.bot.user.id, config.TOKEN,
                                                           ctx.guild_id, name, description, [option])

            await db.execute("INSERT INTO cmds VALUES (?, ?, ?, ?, ?);",
                             (name, response, ctx.author_id, ctx.guild_id, resp["id"]))
            await db.commit()

            async def cmd(_ctx):
                async with db.execute("SELECT resp FROM cmds WHERE cmd_id=?", (_ctx.command_id,)) as _result:
                    await ctx.send(_result.fetchone())

        self.bot.add_slash_command(cmd, name, description, config.guilds, [option])
        await ctx.send(f"Command with name '{name}' successfully created.")

    # TODO: Perms check for command creator/mod+
    @slash.cog_subcommand(base="command", name="remove", description="Remove an existing custom command.",
                          guild_ids=config.guilds)
    async def command_remove(self, ctx, name):
        self.bot.remove_slash_command(name)


def setup(bot):
    bot.add_cog(General(bot))
