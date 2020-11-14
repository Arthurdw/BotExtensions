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
from distutils.util import strtobool
from sys import exit

from config.lang import role_notifier
from discord import Member, Role, Guild
from run import cfg
from utilsx.discord import Cog
from utilsx.discord.objects import Footer


class RoleNotifier(Cog):
    specific = strtobool(cfg["ROLE_NOTIFIER"].get("specific", "false"))

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        if self.specific:
            try:
                self.specific_roles = [int(role) for role in cfg["ROLE_NOTIFIER"].get("roles", "").split(",")
                                       if role != ""]
            except ValueError:
                self.bot.ph.fatal("Invalid value for `ROLE_NOTIFIER` `roles`")
                exit(1)

    async def send_message(self, user: Member, role: Role, guild: Guild, state: str):
        if self.specific:
            if role.id not in self.specific_roles:
                return

        await self.embed(user, role_notifier[state].get("content", "Invalid lang.py").format(role=role, guild=guild),
                         title=role_notifier[state].get("title", "Invalid lang.py"),
                         footer=Footer(
                             role_notifier[state]["footer"].get("text", "Invalid lang.py"),
                             role_notifier[state]["footer"].get("icon", "").format(guild=guild),
                             role_notifier[state]["footer"].get("timestamp", True)),
                         color=(None if role_notifier[state]["color"].get("random", True) else
                                role_notifier[state]["color"].get("color", 0xf0f0f0)))

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if before.roles != after.roles:
            removed = len(before.roles) >= len(after.roles)
            difference = [role for role in (before.roles if removed else after.roles) if
                          role not in (before.roles if not removed else after.roles)]
            for role in difference:
                await self.send_message(after, role, after.guild, "removed" if removed else "added")


def setup(bot):
    try:
        if strtobool(cfg["ROLE_NOTIFIER"].get("enabled", "true")):
            bot.add_cog(RoleNotifier(bot))
    except IndexError:
        bot.ph.fatal("Invalid config for extension `ROLE_NOTIFIER`.")
        bot.ph.fatal("Please read the `README.md` here: "
                     "https://github.com/Arthurdw/BotExtensions/tree/master/role-notifier")
