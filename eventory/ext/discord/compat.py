"""This module serves to bridge the differences between the async and rewrite Discord.py versions."""

import logging
from typing import Callable, Dict, Union

import discord
from discord import Client, Colour, Embed, Message, User
from discord.embeds import EmptyEmbed
from discord.ext.commands import Context
from discord.ext.commands.view import StringView

log = logging.getLogger(__name__)
_REWRITE = discord.version_info[:3] >= (1, 0, 0)

if _REWRITE:
    log.debug("Using the rewrite version of Discord.py, thank you!")
    from discord import DMChannel, TextChannel

    DiscordTextChannel = Union[TextChannel, DMChannel]


    async def send_message(client: Client, channel: DiscordTextChannel, *args, **kwargs) -> Message:
        return await channel.send(*args, **kwargs)


    async def edit_message(client: Client, message: Message, *args, **kwargs) -> Message:
        return await message.edit(*args, **kwargs)


    async def wait_for_message(client: Client, check: Callable[[Message], bool] = None) -> Message:
        return await client.wait_for("message", check=check)


    async def get_context(client: Client, msg: Message) -> Context:
        return await client.get_context(msg)
else:
    import warnings

    warnings.warn(
        "It seems that you're not using the Discord.py rewrite. This extension is written for the rewrite version of Discord.py so it doesn't "
        "necessarily run on your version", ImportWarning)
    from discord import PrivateChannel, Channel

    DiscordTextChannel = Union[PrivateChannel, Channel]


    async def send_message(client: Client, channel: DiscordTextChannel, *args, **kwargs) -> Message:
        return await client.send_message(channel, *args, **kwargs)


    async def edit_message(client: Client, message: Message, *args, **kwargs) -> Message:
        return await client.edit_message(message, *args, **kwargs)


    async def wait_for_message(client: Client, check: Callable[[Message], bool] = None) -> Message:
        return await client.wait_for_message(check=check)


    async def get_context(client: Client, msg: Message) -> Context:
        view = StringView(msg.content)
        ctx = Context(prefix=None, view=view, bot=client, message=msg)

        if client._skip_check(msg.author.id, client.user.id):
            return ctx

        prefix = await client._get_prefix(msg)
        invoked_prefix = prefix

        if isinstance(prefix, str):
            if not view.skip_string(prefix):
                return ctx
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return ctx

        invoker = view.get_word()
        ctx.invoked_with = invoker
        ctx.prefix = invoked_prefix
        ctx.command = client.all_commands.get(invoker)
        return ctx


async def add_embed(client: Union[Client, Context], msg: Union[Context, Message, str] = None, description: Union[str, int] = EmptyEmbed,
                    colour: Union[int, Colour] = EmptyEmbed, *, author: Union[str, Dict, User] = None, footer: Union[str, Dict] = None, **kwargs):
    """Add an Embed to a message.

    Args:
        client: Discord client
        msg: Message to attach the Embed to. You may also pass a Context for convenience.
        description: Description of the Embed
        colour: Colour for the Embed
        author: Author of the Embed.
            Providing a string merely sets the name of the author, the dictionary is fed directly to the set_author method and when provided with a
            User it uses the name and the avatar_url.
        footer: When provided with a string it uses it as the text for the footer and a dictionary is passed to the set_footer function.
    """
    if isinstance(client, Context):
        ctx = client
        client = ctx.bot
        if isinstance(msg, str):
            colour = description
            description = msg
            msg = ctx.message
        elif not msg:
            msg = ctx.message
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
    if msg.author.id == client.user.id:
        await edit_message(client, msg, embed=em)
    else:
        await send_message(client, msg.channel, embed=em)
