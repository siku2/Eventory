import pytest
from discord.ext.commands import Bot

from eventory.ext.discord import EventoryCog


@pytest.fixture(scope="module")
def bot():
    b = Bot("!")
    return b


def test_loading(bot: Bot):
    bot.load_extension("eventory.ext.discord")
    assert bot.cogs.pop("Eventory")
    bot.unload_extension("eventory.ext.discord")

    cog = EventoryCog(bot)
    bot.add_cog(cog)
    assert bot.cogs.pop("Eventory")
    bot.remove_cog("Eventory")
