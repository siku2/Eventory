import inspect
from typing import Callable, Coroutine, Union

import discord
from discord.ext.commands import Bot, Context, group

if discord.version_info[:3] < (1, 0, 0):
    import warnings

    warnings.warn(
        "It seems that you're not using Discord.py rewrite. This extension is written for the rewrite version of Discord.py so it doesn't "
        "necessarily run on your version", ImportWarning)

from eventory import Eventarrator, Eventorial


class DiscordEventarrator(Eventarrator):

    def __init__(self, client: discord.Client, channel: Union[discord.TextChannel, discord.DMChannel],
                 message_check: Callable[[discord.Message], Union[bool, Coroutine]] = None, **kwargs):
        self.client = client
        self.channel = channel

        self.message_check = message_check

    async def output(self, out: str):
        await self.channel.send(out)

    def input_filter(self, msg: discord.Message) -> bool:
        if self.channel.id != msg.channel.id:
            return False
        if self.client._connection.is_bot:  # bots should ignore themselves
            if self.client.user.id == msg.author.id:
                return False

        return True

    async def input_check(self, msg: discord.Message) -> bool:
        if self.message_check:
            ret = self.message_check(msg)
            if inspect.iscoroutine(ret):
                ret = await ret
            return bool(ret)

        if isinstance(self.client, Bot):
            ctx = await self.client.get_context(msg)
            if ctx.command:
                return False

        return True

    async def input(self) -> str:
        while True:
            msg = await self.client.wait_for("message", check=self.input_check)
            if await self.input_check(msg):
                break
        return msg.content


class EventoryCog:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.eventorial = Eventorial(loop=self.bot.loop)

    @group()
    async def eventory(self, ctx: Context):
        """"""
        pass


def setup(bot: Bot):
    bot.add_cog(EventoryCog(bot))
