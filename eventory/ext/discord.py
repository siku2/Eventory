import discord

from eventory import Eventarrator


class DiscordEventarrator(Eventarrator):

    def __init__(self, client: discord.Client, channel: discord.abc.Messageable):
        self.client = client
        self.channel = channel

    async def output(self, out: str):
        await self.channel.send(out)

    async def input(self) -> str:
        msg = await self.client.wait_for("message")
        return msg.content
