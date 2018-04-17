import os

import pytest
from discord.ext.commands import Bot

from eventory.ext.discord import EventoryCog


class MockBot(Bot):
    async def on_ready(self):
        try:
            pass
        finally:
            await self.logout()

    async def on_command_error(self, exception, context):
        await self.logout()
        raise exception


def test_extension_load():
    b = Bot("!")
    b.load_extension("eventory.ext.discord")
    assert b.cogs.pop("Eventory")
    b.unload_extension("eventory.ext.discord")


def test_cog_loading():
    b = Bot("!")
    cog = EventoryCog(b)
    b.add_cog(cog)
    assert b.cogs.pop("Eventory")
    b.remove_cog("Eventory")


@pytest.mark.asyncio
async def test_cog():
    bot = MockBot("!")
    cog = EventoryCog(bot)
    bot.add_cog(cog)
    token = os.environ["DISCORD_TOKEN"]
    await bot.start(token)
