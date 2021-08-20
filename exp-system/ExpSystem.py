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
import random
from asyncio import sleep
from dataclasses import dataclass
from math import sqrt
from os import path, mkdir
from os.path import isfile
from typing import Callable, Awaitable, Any, List

from aiosqlite import Connection, connect, Row
from discord import Message, Member, Guild, Role
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import get
from humanize import intword
from utilsx.discord import Cog

from config.exp_roles import exp_roles
from config.lang import exp_system
from utils import PrintHandler


@dataclass
class _BaseUser:
    # The if of the user.
    id: int
    # The exp the user currently has.
    exp: str
    # The exp threshold which is required for the user to level up.
    exp_next_level: str
    # The user their current level.
    level: int
    # The amount of exp is still required for the user to level.
    left: str


@dataclass
class _User(_BaseUser):
    # The user their current rank compared to the server.
    server_rank: int
    # The total amount of users whom is registered in the database.
    server_total: int


class _DatabaseInteractions:
    """Handles everything which relates with the data of the exp system."""

    def __init__(self, logging: PrintHandler):
        self.log = logging

    def __check_db_file(self):
        """
        Check whether the db folder exists or not, if it doesn't it creates one.
        """
        if not path.isdir("db"):
            self.log.info("[DB] No existing `db` directory found, creating new one...")
            mkdir("db", 0o777)
            self.log.info("[DB] Successfully created new `db` directory.")

    async def __execute_db(self, cb: Callable[[Connection], Awaitable[Any]], check_file: bool = True) -> Any:
        """
        Execute something through a callback.

        @param cb: Callback which will be invoked in the db.
        @param check_file: Whether or not it should check the file, leave this at true unless you are initializing the
                           database.

        @return: The result of the callback.
        """
        self.__check_db_file()

        if check_file and not isfile("db/exp_system.db"):
            await self.__create_db()

        async with connect("db/exp_system.db") as db:
            db.row_factory = Row
            return await cb(db)

    async def __create_db(self):
        """
        Initialize a new database.
        """

        async def helper(conn: Connection):
            self.log.info("[DB] Creating users table...")
            await conn.execute("CREATE TABLE users ("
                               "    id INTEGER PRIMARY KEY,"
                               "    exp INTEGER NOT NULL"
                               ");")
            await conn.commit()
            self.log.info("[DB] Created users table!")

        await self.__execute_db(helper, False)

    @staticmethod
    def convert_exp_to_level(exp: int) -> int:
        """
        Converts a certain exp to the linked level.

        @param exp: The exp to be linked.
        """
        return int(sqrt(exp) / 1.5 - 1)

    @staticmethod
    def convert_level_to_exp(level: int) -> float:
        """
        Converts a certain level to the linked exp which is required for the level.

        @param level: The level to be linked.
        """
        return ((level + 1) * 1.5) ** 2

    def __convert_to_user(self, user_id: int, exp: int, pos: int, total: int):
        """
        Converts a user to an user object, and performs the EXP and level calculations.

        @param user_id: The discord user identifier.
        @param exp: The exp the user currently holds.
        @param pos: The position of the user compared to the server.
        @param total: The total number of registered users.
        """
        lvl = self.convert_exp_to_level(exp)
        exp_next = self.convert_level_to_exp(lvl + 1)
        return _User(user_id, intword(exp), intword(exp_next), lvl, intword(int(exp_next - exp)), pos, total)

    def convert_to_baseuser(self, user_id: int, exp: int):
        """
        Converts a user to an user object, and performs the EXP and level calculations.

        @param user_id: The discord user identifier.
        @param exp: The exp the user currently holds.
        """
        lvl = self.convert_exp_to_level(exp)
        exp_next = self.convert_level_to_exp(lvl + 1)
        return _BaseUser(user_id, intword(exp), intword(exp_next), lvl, intword(int(exp_next - exp)))

    async def get_user_data(self, user_id: int) -> _User:
        """
        Fetch the data from a user and calculate the appropriate values.

        @param user_id: The discord user identifier.
        """
        self.log.info(f"[DB] Fetching experience data from `{user_id}`")

        async def helper(conn: Connection):
            curr = await conn.execute("SELECT exp FROM users WHERE id = ?", (user_id,))
            _exp = tuple(await curr.fetchone() or 0)[0]

            # Fetch the current user their position compared to all registered users.
            curr = await conn.execute(
                "SELECT COUNT(*) FROM users WHERE exp < (SELECT exp FROM users WHERE id = ?) ORDER BY exp DESC;",
                (user_id,))
            _pos = tuple(await curr.fetchone() or 0)[0] + 1

            curr = await conn.execute("SELECT COUNT(*) FROM users;")
            _total_pos = tuple(await curr.fetchone() or 0)[0]

            return _exp, _pos, _total_pos

        return self.__convert_to_user(user_id, *await self.__execute_db(helper))

    async def add_experience(self, user_id: int, experience: int) -> None:
        """
        Give a user experience.

        @param user_id: The discord user identifier.
        @param experience: The experience which the user has gained.
        """
        self.log.info(f"[DB] Adding `{experience}` experience to `{user_id}`")

        async def helper(conn: Connection):
            curr = await conn.execute("SELECT exp FROM users WHERE id = ?", (user_id,))
            res = await curr.fetchone()
            stmt = "UPDATE users SET exp = exp + ? WHERE id = ?" if res \
                else "INSERT INTO users (exp, id) VALUES (?, ?)"

            await conn.execute(stmt, (experience, user_id))
            await conn.commit()

            return tuple(res)[0] if res else 0

        return await self.__execute_db(helper)

    async def get_top(self, amount: int) -> List[_BaseUser]:
        """
        Returns the top x users by exp.

        @param amount: The amount of users that have to be fetched.
        """
        self.log.info(f"[DB] Fetching top `{amount}` members!")

        async def helper(conn: Connection):
            curr = await conn.execute("SELECT id, exp FROM users ORDER BY exp DESC LIMIT ?;", (amount,))
            return map(tuple, await curr.fetchall())

        return list(map(lambda usr: self.convert_to_baseuser(*usr), await self.__execute_db(helper)))


class ExpSystem(Cog):
    """
    Handles everything which relates to the experience system.
    """

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        try:
            self.cfg = self.bot.cfg["LEVELING"]
        except KeyError:
            self.cfg = None
            self.bot.ph.warn("`LEVELING` section missing in `config.cfg`, disabling certain features.")

        try:
            self._notifications_guild = int(self.cfg.get("notifications_guild"))
            self.notifications_channel = int(self.cfg.get("notifications_channel"))
        except (AttributeError, ValueError):
            self.notifications_channel = None

        if not self.cfg or not self.notifications_channel:
            self.bot.ph.warn("`notifications_channel` or `notifications_guild` is missing/mis-configured in the "
                             "`LEVELING` section in `config.cfg`.  This disables the level up notifications.")

        self.roles = exp_roles

        self.db = _DatabaseInteractions(self.bot.ph)

    @Cog.listener()
    async def on_ready(self):
        if not self._notifications_guild:
            self.bot.ph.warn("`notifications_guild` is missing, which is required for both role rewards and level up"
                             " notifications. Both of these features have been disabled!")
            return

        self._notifications_guild = self.bot.get_guild(self._notifications_guild)

        if self.notifications_channel:
            self.notifications_channel = self._notifications_guild.get_channel(self.notifications_channel)

        usable = {}
        for lvl, role in self.roles.items():
            fetched = get(self._notifications_guild.roles, id=role)
            if fetched is None:
                self.bot.ph.warn(f"Role with id `{role}` could not be found in guild `{self._notifications_guild.name}`"
                                 f" (`{self._notifications_guild.id}`), so no role shall be given for level {lvl}. "
                                 f"Please check the `exp_roles.py` file contents.")
                continue

            usable[lvl] = fetched

        self.roles = usable

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        earned = random.randint(1, 6)
        exp: int = await self.db.add_experience(message.author.id, earned) or 0

        new = self.db.convert_exp_to_level(exp + earned)

        role_reward = self.roles.get(new)

        if self._notifications_guild and self.notifications_channel and (
                not (new == 0 or new < 50 or new % 5 != 0) or role_reward):
            ori = self.db.convert_exp_to_level(exp)

            if ori < new:
                async def send_levelup():
                    try:
                        await self.notifications_channel.send(
                            embed=await self.embed(
                                message.channel,
                                exp_system.get("levelup_message").format(author=message.author, lvl=new) +
                                exp_system.get("levelup_message_role").format(role=role_reward),
                                get_embed=True),
                        )
                    except AttributeError:
                        await sleep(0.5)
                        await send_levelup()

                await send_levelup()

        if role_reward:
            async def add_role(role):
                if not isinstance(role, Role):
                    role = self.roles.get(new)

                if isinstance(self._notifications_guild, Guild) and isinstance(role, Role):
                    return await message.author.add_roles(role, reason=f"Leveled up to {new}!")
                await sleep(0.5)
                await add_role(role)

            await add_role(role_reward)

    @commands.command(aliases=['lvl', 'level'])
    async def rank(self, ctx: Context, user: Member = None):
        """
        Retrieve the rank of a user.

        Default user is the person whom has invoked the command.

        Aliases: lvl, level

        Usage examples:
            // Get your own rank
            rank

            // Get the rank of @Arthur
            rank @Arthur
        """
        user = user or ctx.author
        msg = await self.embed(ctx, exp_system.get("fetching"))
        data = await self.db.get_user_data(ctx.author.id)
        await msg.edit(embed=await self.embed(ctx, get_embed=True, color=user.top_role.color,
                                              title=exp_system.get("title").format(user=user),
                                              message=exp_system.get("message").format(user=user, data=data)))

    @commands.command()
    async def top(self, ctx: Context, amount: int = 10):
        """
        Fetch the top x members with the highest exp.

        Default amount is 10.

        Usage examples:
            // Get the top 10 members
            top

            // Get the top 15 members
            top 123456789987654321
        """
        if 1 <= amount <= exp_system.get("max_top", 25):
            return await self.embed(ctx, "\n".join(
                [exp_system.get("top_line").format(idx=idx + 1, user=usr) for idx, usr in
                 enumerate(await self.db.get_top(amount))]), title=exp_system.get("top_title"))

        await ctx.send(embed=await self.embed(ctx, exp_system.get("top_msg"), get_embed=True), delete_after=10)


def setup(bot):
    bot.add_cog(ExpSystem(bot))
