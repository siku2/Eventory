import logging
from typing import Dict, Optional, Union

from discord.ext.commands import Bot, Context, group

from eventory import Eventorial, Eventructor
from .compat import DiscordTextChannel, add_embed
from .narrator import DiscordEventarrator

log = logging.getLogger(__name__)


class EventoryCog:
    """Eventory, yay

    I have no idea what to write here so it's just gonna stay like this for now
    """
    instructors: Dict[int, Eventructor]

    SUCCESS_COLOUR = 0x15BA00
    ERROR_COLOUR = 0xFF0000
    INFO_COLOUR = 0xC8FF6A

    def __init__(self, bot: Bot, *, directory: str = None):
        self.bot = bot
        self.eventorial = Eventorial(directory=directory, loop=self.bot.loop)
        self.instructors = {}

    def get_instructor(self, channel: Union[int, Context, DiscordTextChannel]) -> Optional[Eventructor]:
        if isinstance(channel, Context):
            channel = channel.message.channel
        if isinstance(channel, DiscordTextChannel.__args__):
            channel = channel.id
        instructor = self.instructors.get(channel, None)
        if instructor:
            if instructor.stopped:
                log.info(f"Found {instructor}, but it's already stopped!")
                self.instructors.pop(channel)
            else:
                return instructor
        return None

    @group(pass_context=True)
    async def eventory(self, ctx: Context):
        """Yay"""
        ...

    @eventory.command(pass_context=True)
    async def load(self, ctx: Context, source: str):
        """Load an Eventory"""
        try:
            story = await self.eventorial.load(source)
        except:
            log.exception(f"Couldn't load Eventory {source}")
            await add_embed(ctx, f"Couldn't load \"{source}\"", self.ERROR_COLOUR)
        else:
            log.info(f"loaded {story}")
            await add_embed(ctx, f"Loaded \"{story.title}\" by {story.author}", self.SUCCESS_COLOUR)

    @eventory.command(pass_context=True)
    async def play(self, ctx: Context, name: str):
        """Play an Eventory"""
        if self.get_instructor(ctx):
            await add_embed(ctx, "There's already an Eventory running in this chat!", self.ERROR_COLOUR)
            return
        story = self.eventorial.get(name, None)
        if not story:
            await add_embed(ctx, f"No Eventory \"{name}\" found", self.ERROR_COLOUR)
            return
        narrator = DiscordEventarrator(self.bot, ctx.message.channel)
        instructor = story.narrate(narrator)
        self.instructors[ctx.message.channel.id] = instructor
        await add_embed(ctx, f"Playing \"{story.title}\" by {story.author}", self.SUCCESS_COLOUR)
        await instructor.play()
        log.info(f"playing {story} in {ctx.message.channel}")

    @eventory.command(pass_context=True)
    async def info(self, ctx: Context, story: str = None):
        """Get some information about an Eventory"""
        if not story:
            instructor = self.get_instructor(ctx)
            if not instructor:
                await add_embed(ctx, "No Eventory currently running in this chat", self.ERROR_COLOUR)
                return
            story = instructor.eventory
        else:
            story = self.eventorial.get(story, None)
            if not story:
                await add_embed(ctx, f"No Eventory \"{story}\" found", self.ERROR_COLOUR)
                return
        await add_embed(ctx, title=story.title, description=story.description, footer=f"Version {story.version}", author=story.author,
                        colour=self.INFO_COLOUR)

    @eventory.command(pass_context=True)
    async def abort(self, ctx: Context):
        """Abort the current Eventory in this channel."""
        instructor = self.get_instructor(ctx)
        if instructor:
            instructor.stop()
            log.info(f"stopped {instructor} in {ctx.message.channel}")
        else:
            await add_embed(ctx, "No Eventory currently running in this chat", self.ERROR_COLOUR)


EventoryCog.__name__ = "Eventory"
