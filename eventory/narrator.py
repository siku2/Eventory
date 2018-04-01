import abc
import sys
from io import TextIOBase


class Eventarrator(metaclass=abc.ABCMeta):
    """There he goes again with the Eventory + narrator combination. Are you sick of it yet?"""

    @abc.abstractmethod
    async def output(self, out: str):
        raise NotImplementedError

    @abc.abstractmethod
    async def input(self) -> str:
        raise NotImplementedError


class StreamEventarrator(Eventarrator):
    def __init__(self, in_stream: TextIOBase = sys.stdin, out_stream: TextIOBase = sys.stdout):
        self.in_stream = in_stream
        self.out_stream = out_stream

    async def output(self, out: str):
        self.out_stream.write(out)
        self.out_stream.flush()

    async def input(self) -> str:
        return self.in_stream.readline()
