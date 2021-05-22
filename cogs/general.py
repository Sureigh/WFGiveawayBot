# -*- coding: utf-8 -*-
import typing
import pickle

import discord
from discord.ext import commands
import aiosqlite
import asyncio

import configs


class General(commands.Cog):
    """A cog for general, uncategorized commands."""

    def __init__(self, bot):
        self.bot = bot
        aiosqlite.register_adapter(commands.Command, lambda x: pickle.dumps(x))
        bot.loop.create_task(self.cmd_init())

        async def react_and_wait(msg: discord.Message, **kwargs) -> tuple:
            """
            Allows for users to respond with either a string or an emoji representation of it.
            The kwarg should be written as {"str_repr"=emoji}.
            """
            for emote in kwargs.values():
                await msg.add_reaction(emote)

            def check_msg(_msg):
                return all((_msg.content in kwargs.keys(), _msg.channel == msg.channel, _msg.author == msg.author))

            def check_reaction(_reaction, user):
                return all((_reaction.emoji in kwargs.keys(), _reaction.message == msg, user == msg.author))

            # ?tag wait_for multiple in dpy for more info
            done, pending = await asyncio.wait(
                (self.bot.wait_for("message", check=check_msg),
                 self.bot.wait_for("reaction_add", check=check_reaction)),
                return_when=asyncio.FIRST_COMPLETED, timeout=60  # TODO: Configurable timeout
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
                return coro.content, "message", coro
            else:
                reaction, _ = coro
                return {v: k for k, v in kwargs.items()}.get(str(reaction.emoji)), "reaction_add", coro
        bot.react_and_wait = react_and_wait

    # Originally inspired by https://github.com/eunwoo1104/slash-bot/blob/master/main.py
    # Actual logic of custom commands
    async def cmd_init(self):
        """Loads custom commands into the bot."""
        await self.bot.wait_until_ready()

        async with aiosqlite.connect(configs.DATABASE_NAME) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT cmd FROM cmds") as cursor:
                async for row in cursor:
                    self.bot.add_command(*row)

    @commands.group(name="command", aliases=["cmd", "c"])
    @commands.check_any(commands.has_guild_permissions(manage_messages=True), commands.has_any_role())
    async def cmd(self, ctx):
        """All custom command related commands."""
        if not ctx.invoked_subcommand:
            await ctx.send_help(self.cmd)

    @cmd.command(name="create", aliases=["c", "new", "n"], description="Create a custom command.")
    async def command_create(self, ctx, name, *, response):
        # TODO: add a configurable amount of custom commands per donator,
        #  and then check that a donator has not surpassed that amount

        async with aiosqlite.connect(configs.DATABASE_NAME) as db:
            # Checks if command already exists
            async with db.execute("SELECT * FROM cmds WHERE name=? AND guild_id=?", (name, ctx.guild_id)) as cursor:
                result = await cursor.fetchone()

            if result:
                if not ctx.author.guild_permissions.manage_messages:  # If not moderator
                    return await ctx.send("A command with this name already exists.")

                msg = await ctx.send("A command with this name already exists.\n"
                                     "Would you like to overwrite it?\n\n**Y / N**")
                # pep8 moment xd
                reaction = await ctx.bot.react_and_wait(msg, Y=":regional_indicator_y:", N=":regional_indicator_n:")
                if "Y" in reaction:
                    # TODO: Invoke subcommand
                    pass

                await msg.delete()
                if "message" in reaction:
                    await reaction[-1].add_reaction(":white_check_mark:")
                return

            @commands.command(name=name)
            @commands.check(lambda _ctx: _ctx.guild.id == ctx.guild.id)
            async def cmd_template(_ctx):
                await _ctx.send(response)

            await db.execute("INSERT INTO cmds VALUES (?, ?, ?, ?);",
                             (name, ctx.guild.id, ctx.author.id, cmd_template))
            await db.commit()

        await ctx.send(f"Command with name '{name}' successfully created.")

    @cmd.commands(name="remove", aliases=["rm", "delete", "d"], description="Remove an existing custom command.")
    async def command_remove(self, ctx, name):
        async with aiosqlite.connect(configs.DATABASE_NAME) as db:
            async with db.execute("SELECT  FROM cmds WHERE name=? AND guild_id=?",
                                  (name, ctx.guild_id)) as cursor:
                owner, cmd_id = await cursor.fetchone()
            if not (ctx.author.guild_permissions.manage_messages or ctx.author_id == owner):
                raise commands.MissingPermissions(["manage_messages"])

            await db.execute("DELETE FROM cmds WHERE name=? AND guild_id=?", (name, ctx.guild_id))
            await db.commit()
        await ctx.send(f"Command with name '{name}' successfully removed.")

    @cmd.commands(name="update", aliases=["u", "edit", "e"],
                  description="Update an existing custom command's name, response and/or description.")
    async def update_command(self, ctx, cmd, name=None, response=None, description=None):
        pass


def setup(bot):
    bot.add_cog(General(bot))
