from typing import Union

import discord

from eventory import Eventarrator


class DiscordEventarrator(Eventarrator):

    def __init__(self, client: discord.Client, channel: Union[discord.TextChannel, discord.DMChannel]):
        self.client = client
        self.channel = channel

    async def output(self, out: str):
        await self.channel.send(out)

    def input_check(self, msg: discord.Message) -> bool:
        if self.channel.id != msg.channel.id:
            return False
        if self.client._connection.is_bot:  # bots should ignore themselves
            if self.client.user.id == msg.author.id:
                return False

        return True

    async def input(self) -> str:
        msg = await self.client.wait_for("message", check=self.input_check)
        return msg.content
