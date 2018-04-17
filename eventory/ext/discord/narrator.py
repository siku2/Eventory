import inspect
import logging
from collections import Iterable, deque

from discord import Client, Message
from discord.ext.commands import Bot

from eventory import Eventarrator
from .compat import DiscordTextChannel, get_context, send_message, wait_for_message

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
        msg: Message = await send_message(self.client, self.channel, out)
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
            ctx = await get_context(self.client, msg)
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
            msg = await wait_for_message(self.client, check=self.input_filter)
            if await self.input_check(msg):
                break
        return msg.content
