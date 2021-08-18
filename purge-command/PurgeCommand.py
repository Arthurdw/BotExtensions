# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2019-2020 Arthur

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from functools import partial
from typing import Union

from discord import Member, NotFound
from discord.abc import GuildChannel
from discord.ext import commands
from discord.ext.commands import Context, Greedy
from discord.utils import get
from utilsx.discord import Cog

from config.lang import purge_command


class PurgeCommand(Cog):
    """
    This handles the purge command.
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        try:
            purge_allowed = self.bot.cfg["MODERATION"]["purge"]
        except KeyError:
            raise Exception("Missing `purge` attribute in `MODERATION` part of config file.")

        def convert_if_number(value: str) -> Union[str, int]:
            try:
                return int(value)
            except ValueError:
                return value

        self.allowed = [convert_if_number(p.strip()) for p in purge_allowed.split(",")]

    @commands.command()
    async def purge(self, ctx: Context, count: int = 100, authors: Greedy[Union[Member]] = None):
        """
        Removes a certain amount of messages in the current channel.
        This can be filtered by certain members.

        Default amount is 100.

        Usage examples:
            // Removes 10 messages regardless from whom.
            purge 10

            // Removes 10 messages from @Arthur and a user whom has the id of 640625683797639181.
            purge 10 @Arthur 640625683797639181
        """
        if not isinstance(ctx.channel, GuildChannel):
            return await self.embed(ctx, "This command can only be used in a discord server!")

        getter = partial(get, ctx.author.roles)
        if not any(getter(id=role) is not None if isinstance(role, int) else getter(name=role) is not None for role in
                   self.allowed):
            return await self.embed(ctx, "You don't have the required role!")

        _ending = f" {purge_command.get('from')} " + ", ".join([a.mention for a in authors]) if authors is not None else ""
        msg = await self.embed(ctx, purge_command.get("started").format(count=count, ending=_ending))
        deleted = await ctx.channel.purge(limit=count, check=lambda m: authors is None or m.author in authors)
        em = await self.embed(ctx, purge_command.get("finished").format(count=len(deleted), ending=_ending), get_embed=True, color=purge_command.get("finished_color", 0x00ff00))

        try:
            await msg.edit(embed=em, delete_after=10)
        except NotFound:
            await ctx.send(embed=em, delete_after=10)


def setup(bot):
    bot.add_cog(PurgeCommand(bot))
