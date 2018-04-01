import discord

from eventory import Eventarrator


class DiscordEventarrator(Eventarrator):

    def __init__(self, channel: discord.abc.Messageable):
        self.channel = channel

    async def output(self, out):
        await self.channel.send(out)
