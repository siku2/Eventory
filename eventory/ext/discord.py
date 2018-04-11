"""Discord.py extension for Eventory.

This module allows Eventory to be used with the Discord.py library. It contains various classes to make integration as easy as possible while still
allowing Eventory to unfold its power.

If you're using the commands extension provided by the Discord.py library you can either use the EventoryCog or you can load it as an extension.

Example:
    To load the Eventory integration as an extension::

        bot.load_ext("eventory.ext.discord")

    To load the cog::

        cog = EventoryCog(bot)
        bot.add_cog(cog)

If you aren't using the commands library you can use the DiscordEventarrator directly to interface with Eventory.
"""

import inspect
import logging
from collections import Iterable, deque
from typing import Dict, Optional, Union

import discord
from discord import Client, Colour, Embed, Message, User
from discord.embeds import EmptyEmbed
from discord.ext.commands import Bot, Context, group

from eventory import Eventarrator, Eventorial, Eventructor

_REWRITE = discord.version_info[:3] >= (1, 0, 0)

if _REWRITE:
    from discord import DMChannel, TextChannel

    DiscordTextChannel = Union[TextChannel, DMChannel]
else:
    import warnings
    from discord import PrivateChannel, Channel

    DiscordTextChannel = Union[PrivateChannel, Channel]
    warnings.warn(
        "It seems that you're not using the Discord.py rewrite. This extension is written for the rewrite version of Discord.py so it doesn't "
        "necessarily run on your version", ImportWarning)

log = logging.getLogger(__name__)


class DiscordEventarrator(Eventarrator):
    """The Discord Eventarrator that does the actual work.

    Args:
        client: Client to use
        channel: TextChannel to play the Eventory in
        users (Optional[Union[User, Sequence[User]]]): The user or a list of users who play(s) the Eventory
        message_check (Optional[Callable[[Message], Union[bool, Awaitable[bool]]]): A function or coroutine function which takes a message and returns
        a boolean to denote whether this message is valid input or not

    Attributes:
        client (Client)
        channel (DiscordTextChannel)
        users (Optional[Set[User]]): Set of users to listen to
        message_check (Optional[Callable[[Message], Union[bool, Awaitable[bool]]])
        options (dict): Leftover keyword arguments passed to the constructor
        sent_messages (deque): Deque containing the ids of the last 10 messages sent by the Eventarrator
    """

    def __init__(self, client: Client, channel: DiscordTextChannel, **options):
        self.client = client
        self.channel = channel
        users = options.pop("users", None)
        if users:
            if isinstance(users, Iterable):
                users = tuple(users)
            else:
                users = (users,)
        self.users = users
        self.message_check = options.pop("message_check", None)
        self.options = options
        self.sent_messages = deque(maxlen=10)

    async def output(self, out: str):
        """Send the output to the channel.

        Args:
            out: Text to send
        """
        if not out:
            log.warning("Not outputting empty message")
            return
        msg: Message = await self.channel.send(out)
        self.sent_messages.appendleft(msg.id)
        log.debug(f"sent \"{out}\"")

    def input_filter(self, msg: Message) -> bool:
        """Basic message filter passed to the wait_for function.

        This function makes sure that the message isn't part of the messages the scripts itself sent (by checking it against the sent_messages deque),
        that the message was sent in the correct channel, that, if a user target is provided, the message was sent by one of them and that the author
        isn't a bot.

        Args:
            msg: Message to check

        Returns:
            bool: Whether the message should be ignored or not
        """
        if self.channel.id != msg.channel.id:
            log.debug(f"Ignoring {msg} (wrong channel)!")
            return False
        if msg.id in self.sent_messages:
            log.debug(f"Ignoring {msg} (sent by Eventory)!")
            return False
        if self.users and msg.author not in self.users:
            log.debug(f"Ignoring {msg} (not sent by {self.users})!")
            return False
        if msg.author.bot:  # bots should be ignored
            log.debug(f"Ignoring {msg} (Message sent by bot)!")
            return False

        return True

    async def input_check(self, msg: Message) -> bool:
        """More advanced filter to check whether the message is truly meant for Eventory.

        When there's a message_check provided, this function will directly return its result. If the provided client is a Bot instance from the
        commands extension, this function checks whether the message triggers a command in which case it will return False.

        Args:
            msg: Message to check

        Returns:
            bool: Whether the message should be ignored or not
        """
        if self.message_check:
            log.debug(f"Running custom message check!")
            ret = self.message_check(msg)
            if inspect.iscoroutine(ret):
                ret = await ret
            return bool(ret)

        if isinstance(self.client, Bot):
            ctx = await self.client.get_context(msg)
            if ctx.command:
                log.debug(f"Ignoring {msg} (Command detected)!")
                return False

        return True

    async def input(self) -> str:
        """Get a valid input.

        Wait for a message, run it against the input_filter and input_check and if it passes, return the content.

        Returns:
            str: Valid input
        """
        while True:
            msg = await self.client.wait_for("message", check=self.input_filter)
            if await self.input_check(msg):
                break
        return msg.content


async def add_embed(msg: Union[Context, Message], description: str = EmptyEmbed, colour: Union[int, Colour] = EmptyEmbed, *,
                    author: Union[str, Dict, User] = None, footer: Union[str, Dict] = None, **kwargs):
    """Add an Embed to a message.

    Args:
        msg: Message to attach the Embed to. You may also pass a Context for convenience.
        description: Description of the Embed
        colour: Colour for the Embed
        author: Author of the Embed.
            Providing a string merely sets the name of the author, the dictionary is fed directly to the set_author method and when provided with a
            User it uses the name and the avatar_url.
        footer: When provided with a string it uses it as the text for the footer and a dictionary is passed to the set_footer function.
    """
    if isinstance(msg, Context):
        msg = msg.message
    em = Embed(description=description, colour=colour, **kwargs)
    if author:
        if isinstance(author, dict):
            em.set_author(**author)
        elif isinstance(author, User):
            em.set_author(name=author.name, icon_url=author.avatar_url)
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

    def get_instructor(self, channel: Union[int, Context, DiscordTextChannel]) -> Optional[Eventructor]:
        if isinstance(channel, Context):
            channel = channel.channel
        if isinstance(channel, DiscordTextChannel):
            channel = channel.id
        instructor = self.instructors.get(channel, None)
        if instructor:
            if instructor.stopped:
                log.info(f"Found {instructor}, but it's already stopped!")
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
            log.exception(f"Couldn't load Eventory {source}")
            await add_embed(ctx, f"Couldn't load \"{source}\"", ERROR_COLOUR)
        else:
            log.info(f"loaded {story}")
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
        log.info(f"playing {story} in {ctx.channel}")

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
            log.info(f"stopped {instructor} in {ctx.channel}")
        else:
            await add_embed(ctx, "No Eventory currently running in this chat", ERROR_COLOUR)


EventoryCog.__name__ = "Eventory"


def setup(bot: Bot):
    """Convenience method to load the cog like an extension.

    Basically this method adds the EventoryCog to the bot so you can use

    Example:
        Setting up the extension is as easy as::

            bot.load_extension("eventory.ext.discord")"

    Args:
        bot: The bot to setup
    """
    bot.add_cog(EventoryCog(bot))
    log.info("loaded Eventory extension!")
