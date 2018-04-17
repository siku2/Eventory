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

import logging

from discord.ext.commands import Bot

from .cog import EventoryCog
from .narrator import DiscordEventarrator

log = logging.getLogger(__name__)


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
