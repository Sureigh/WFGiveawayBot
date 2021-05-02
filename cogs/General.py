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
        bot.loop.create_task(self.cmd_init())

    # Borrowed a snippet from https://github.com/eunwoo1104/slash-bot/blob/master/main.py
    # Actual logic of custom commands
    option = manage_commands.create_option("Hidden", "Send reply hidden.", bool, False)

    async def cmd_template(self, _ctx, hidden=None):
        async with aiosqlite.connect(self.bot.db) as _db:
            async with _db.execute("SELECT resp FROM cmds WHERE name=?", (_ctx.name,)) as _result:
                await _ctx.send(*await _result.fetchone(), hidden=bool(hidden))

    async def cmd_init(self):
        """Loads custom commands into the bot."""
        await self.bot.wait_until_ready()

        async with aiosqlite.connect(self.bot.db) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM cmds") as cursor:
                rows = await cursor.fetchall()

            for row in rows:
                self.bot.slash.add_slash_command(
                    self.cmd_template, row["name"], row["desc"], [row["guild_id"]], [self.option]
                )
            await self.bot.slash.sync_all_commands()

    @slash.cog_subcommand(base="command", name="create", description="Create a custom command.",
                          guild_ids=config.guilds)
    async def command_create(self, ctx, name, response, description=None):
        if not (moderator := ctx.author.guild_permissions.manage_messages):  # TODO: if not mod or donator
            raise commands.MissingPermissions(["manage_messages"])
        elif len(name) > 32:
            return await ctx.send("Command name is too long! (Over 32 characters)")
        elif len(await manage_commands.get_all_commands(ctx.bot.user.id, ctx.bot.http.token, ctx.guild_id)) >= 100:
            return await ctx.send("Too many commands in guild! (Limit is 100 commands per guild)")
            # TODO: I don't think this'll ever become a problem; but if it does,
            #  consider maybe creating a "helper" bot that creates more commands to bypass this limit?

        # TODO: add a configurable amount of custom commands per donator,
        #  and then check that a donator has not surpassed that amount

        async with aiosqlite.connect(ctx.bot.db) as db:
            # Checks if command already exists
            async with db.execute("SELECT * FROM cmds WHERE name=? AND guild_id=?", (name, ctx.guild_id)) as cursor:
                result = await cursor.fetchone()

            if bool(result):
                if not moderator:
                    return await ctx.send("A command with this name already exists.")
                else:
                    await ctx.send("A command with this name already exists.\n"
                                   "Would you like to overwrite it?\n\n**Y / N**")
                    return

                    # TODO: ask if yes or no to overwrite function

            resp = await manage_commands.add_slash_command(
                ctx.bot.user.id, ctx.bot.http.token, ctx.guild_id, name, description, [self.option]
            )

            await db.execute("INSERT INTO cmds VALUES (?, ?, ?, ?, ?, ?);",
                             (name, response, description, ctx.author_id, ctx.guild_id, resp["id"]))
            await db.commit()

        self.bot.slash.add_slash_command(self.cmd_template, name, description, config.guilds, [self.option])
        await ctx.send(f"Command with name '{name}' successfully created.")

    # TODO: Perms check for command creator/mod+
    @slash.cog_subcommand(base="command", name="remove", description="Remove an existing custom command.",
                          guild_ids=config.guilds)
    async def command_remove(self, ctx, name):
        async with aiosqlite.connect(ctx.bot.db) as db:
            async with db.execute("SELECT user, cmd_id FROM cmds WHERE name=? AND guild_id=?",
                                  (name, ctx.guild_id)) as cursor:
                owner, cmd_id = await cursor.fetchone()
            if not (ctx.author.guild_permissions.manage_messages or ctx.author_id == owner):
                raise commands.MissingPermissions(["manage_messages"])

            await manage_commands.remove_slash_command(ctx.bot.user.id, ctx.bot.http.token, ctx.guild_id, cmd_id)
            await db.execute("DELETE FROM cmds WHERE name=? AND guild_id=?", (name, ctx.guild_id))
        await ctx.send(f"Command with name '{name}' successfully removed.")


def setup(bot):
    bot.add_cog(General(bot))
