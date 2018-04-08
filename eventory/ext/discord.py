import inspect
from collections import Iterable, deque
from typing import Callable, Coroutine, Dict, Optional, Sequence, Union

import discord
from discord import Client, Colour, DMChannel, Embed, Message, TextChannel, User
from discord.embeds import EmptyEmbed
from discord.ext.commands import Bot, Context, group

from eventory import Eventarrator, Eventorial, Eventructor

if discord.version_info[:3] < (1, 0, 0):
    import warnings

    warnings.warn(
        "It seems that you're not using Discord.py rewrite. This extension is written for the rewrite version of Discord.py so it doesn't "
        "necessarily run on your version", ImportWarning)


class DiscordEventarrator(Eventarrator):

    def __init__(self, client: Client, channel: Union[TextChannel, DMChannel], users: Union[User, Sequence[User]] = None, *,
                 message_check: Callable[[Message], Union[bool, Coroutine]] = None, **kwargs):
        self.client = client
        self.channel = channel
        if users:
            if isinstance(users, Iterable):
                users = list(users)
            else:
                users = [users]
        self.users = users
        self.message_check = message_check
        self.options = kwargs
        self.sent_messages = deque(maxlen=3)

    async def output(self, out: str):
        msg: Message = await self.channel.send(out)
        self.sent_messages.appendleft(msg.id)

    def input_filter(self, msg: Message) -> bool:
        if msg.id in self.sent_messages:
            return False
        if self.channel.id != msg.channel.id:
            return False
        if self.users and msg.author not in self.users:
            return False

        # noinspection PyProtectedMember
        if self.client._connection.is_bot:  # bots should ignore themselves
            if self.client.user.id == msg.author.id:
                return False

        return True

    async def input_check(self, msg: Message) -> bool:
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


async def add_embed(msg: Union[Context, Message], description: str = EmptyEmbed, colour: Union[int, Colour] = EmptyEmbed,
                    author: Union[str, Dict] = None, footer: Union[str, Dict] = None, **kwargs):
    if isinstance(msg, Context):
        msg = msg.message
    em = Embed(description=description, colour=colour, **kwargs)
    if author:
        if isinstance(author, dict):
            em.set_author(**author)
        else:
            em.set_author(name=author)
    if footer:
        if isinstance(footer, dict):
            em.set_footer(**footer)
        else:
            em.set_footer(text=footer)
    await msg.edit(embed=em)


SUCCESS_COLOUR = 0x15BA00
ERROR_COLOUR = 0xFF0000
INFO_COLOUR = 0xC8FF6A


class EventoryCog:
    """Eventory, yay

    I have no idea what to write here so it's just gonna stay like this for now
    """
    instructors: Dict[int, Eventructor]

    def __init__(self, bot: Bot, *, directory: str = None):
        self.bot = bot
        self.eventorial = Eventorial(directory=directory, loop=self.bot.loop)
        self.instructors = {}

    def get_instructor(self, channel: Union[int, Context, DMChannel, TextChannel]) -> Optional[Eventructor]:
        if isinstance(channel, Context):
            channel = channel.channel
        if isinstance(channel, (DMChannel, TextChannel)):
            channel = channel.id
        instructor = self.instructors.get(channel, None)
        if instructor:
            if instructor.stopped:
                self.instructors.pop(channel)
            else:
                return instructor
        return None

    @group()
    async def eventory(self, ctx: Context):
        """Yay"""
        ...

    @eventory.command()
    async def load(self, ctx: Context, source: str):
        """Load an Eventory"""
        try:
            story = await self.eventorial.load(source)
        except:
            await add_embed(ctx, f"Couldn't load \"{source}\"", ERROR_COLOUR)
        else:
            await add_embed(ctx, f"Loaded \"{story.title}\" by {story.author}", SUCCESS_COLOUR)

    @eventory.command()
    async def play(self, ctx: Context, story: str):
        """Play an Eventory"""
        if self.get_instructor(ctx):
            await add_embed(ctx, "There's already an Eventory running in this chat!", ERROR_COLOUR)
            return
        story = self.eventorial.get(story, None)
        if not story:
            await add_embed(ctx, f"No Eventory \"{story}\" found", ERROR_COLOUR)
            return
        narrator = DiscordEventarrator(self.bot, ctx.channel)
        instructor = story.narrate(narrator)
        self.instructors[ctx.channel.id] = instructor
        await add_embed(ctx, f"Playing \"{story.title}\" by {story.author}", SUCCESS_COLOUR)
        await instructor.play()

    @eventory.command()
    async def info(self, ctx: Context, story: str = None):
        """Get some information about an Eventory"""
        if not story:
            instructor = self.get_instructor(ctx)
            if not instructor:
                await add_embed(ctx, "No Eventory currently running in this chat", ERROR_COLOUR)
                return
            story = instructor.eventory
        else:
            story = self.eventorial.get(story, None)
            if not story:
                await add_embed(ctx, f"No Eventory \"{story}\" found", ERROR_COLOUR)
                return
        await add_embed(ctx, title=story.title, description=story.description, footer=f"Version {story.version}", author=story.author,
                        colour=INFO_COLOUR)

    @eventory.command()
    async def abort(self, ctx: Context):
        """Abort the current Eventory in this channel."""
        instructor = self.get_instructor(ctx)
        if instructor:
            instructor.stop()
        else:
            await add_embed(ctx, "No Eventory currently running in this chat", ERROR_COLOUR)


EventoryCog.__name__ = "Eventory"


def setup(bot: Bot):
    bot.add_cog(EventoryCog(bot))
