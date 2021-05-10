# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord_slash import cog_ext as slash
from discord_slash.utils import manage_commands

import aiosqlite
import asyncio

import config


class General(commands.Cog):
    """A cog for general, uncategorized commands."""

    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.cmd_init())

        async def react_and_wait(msg: discord.Message, **kwargs: str) -> str:
            for emote in kwargs.values():
                await msg.add_reaction(emote)

            def check_msg(_msg):
                return all((_msg.content in kwargs.keys(), _msg.channel == msg.channel, _msg.author == msg.author))

            def check_reaction(reaction, user):
                return all((reaction.message == msg, reaction.emoji in kwargs.keys(), user == msg.author))

            # ?tag wait_for multiple in dpy for more info
            done, pending = await asyncio.wait(
                (self.bot.wait_for('message', check=check_msg),
                 self.bot.wait_for('reaction_add', check=check_reaction)),
                return_when=asyncio.FIRST_COMPLETED, timeout=60
            )
            try:
                coro = done.pop().result()
            except IndexError:
                return await msg.channel.send("Choice timed out.")

            for future in done:
                future.exception()
            for future in pending:
                future.cancel()

            # If wait_for_message
            if isinstance(coro, discord.Message):
                return coro.content
            else:
                reaction, _ = coro
                return {v: k for k, v in kwargs.items()}.get(str(reaction.emoji))

        bot.react_and_wait = react_and_wait

    # Borrowed a snippet from https://github.com/eunwoo1104/slash-bot/blob/master/main.py
    # Actual logic of custom commands
    option = manage_commands.create_option("Hidden", "Send reply hidden.", bool, False)

    async def cmd_template(self, ctx, hidden=None):
        async with aiosqlite.connect(self.bot.db) as db:
            async with db.execute("SELECT resp FROM cmds WHERE name=?", (ctx.name,)) as _result:
                await ctx.send(*await _result.fetchone(), hidden=bool(hidden))

    async def cmd_init(self):
        """Loads custom commands into the bot."""
        await self.bot.wait_until_ready()

        async with aiosqlite.connect(self.bot.db) as db:
            # Add all commands
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM cmds") as cursor:
                rows = await cursor.fetchall()

            for row in rows:
                self.bot.slash.add_slash_command(
                    self.cmd_template, row["name"], row["desc"], [row["guild_id"]], [self.option]
                )
            await self.bot.slash.sync_all_commands()

            # Update command guild IDs
            # I know config.guilds is a thing, but hey, I'm trying to learn to be creative, okay? Let me go with it.
            async with db.execute("SELECT DISTINCT guild_id FROM cmds") as cursor:
                guilds = [row["guild_id"] for row in await cursor.fetchall()]

            for guild_id in guilds:
                resp = await manage_commands.get_all_commands(self.bot.user.id, self.bot.http.token, guild_id)
                resp = [(cmd["id"], cmd["name"]) for cmd in resp]

                async with db.execute("SELECT name FROM cmds WHERE guild_id=?", (guild_id,)) as cursor:
                    cmds = await cursor.fetchall()
                await db.executemany("UPDATE cmds SET cmd_id=? WHERE name=?", resp)
                await db.commit()

    @slash.cog_subcommand(base="command", name="create", description="Create a custom command.",
                          guild_ids=config.guilds)
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), commands.has_any_role())
    async def command_create(self, ctx, name, response, description=None):
        if len(name) > 32:
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
                if not ctx.author.guild_permissions.manage_messages:  # If not moderator
                    return await ctx.send("A command with this name already exists.")

                msg = await ctx.send("A command with this name already exists.\n"
                                     "Would you like to overwrite it?\n\n**Y / N**")
                # pep8 moment xd
                reaction = await ctx.bot.react_and_wait(msg, Y=":regional_indicator_y:", N=":regional_indicator_n:")
                if reaction == "Y":
                    # TODO: Invoke subcommand
                    pass

                # TODO: consider a cleanup command that removes reactions or something idk i'm tired bye

            resp = await manage_commands.add_slash_command(
                ctx.bot.user.id, ctx.bot.http.token, ctx.guild_id, name, description, [self.option]
            )

            await db.execute("INSERT INTO cmds VALUES (?, ?, ?, ?, ?, ?);",
                             (name, response, description, ctx.author_id, ctx.guild_id, resp["id"]))
            await db.commit()

        self.bot.slash.add_slash_command(self.cmd_template, name, description, config.guilds, [self.option])
        await ctx.send(f"Command with name '{name}' successfully created.")

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
            await db.commit()
        await ctx.send(f"Command with name '{name}' successfully removed.")

    @slash.cog_subcommand(base="command", name="update",
                          description="Update an existing custom command's name, response and/or description.",
                          guild_ids=config.guilds)
    async def update_command(self, ctx, current_name, name=None, response=None, description=None):
        pass


def setup(bot):
    bot.add_cog(General(bot))
