"""Module containing the abc for an Eventarrator and some built-in Eventarrators."""

import abc
import sys
from io import TextIOBase


class Eventarrator(metaclass=abc.ABCMeta):
    """An Eventarrator is the output and input of an Eventructor."""

    @abc.abstractmethod
    async def output(self, out: str):
        """Method to output a string so it gets to the user.

        Args:
            out: String to output
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def input(self) -> str:
        """Method to receive input from the user.

        Returns:
            str: Input provided by the user
        """
        raise NotImplementedError


class StreamEventarrator(Eventarrator):
    """A simple implementation of an Eventarrator to write and read from streams.

    Args:
        in_stream: Stream to use to receive input
        out_stream: Stream to write to to output

    Attributes:
        in_stream: Stream to use to receive input
        out_stream: Stream to write to to output
    """

    def __init__(self, in_stream: TextIOBase = sys.stdin, out_stream: TextIOBase = sys.stdout):
        self.in_stream = in_stream
        self.out_stream = out_stream

    async def output(self, out: str):
        """Write to the out_stream and flush.

        Args:
            out: Text to write
        """
        self.out_stream.write(out)
        self.out_stream.flush()

    async def input(self) -> str:
        """Reads from the in_stream.

        Returns:
            str: String read from stream.
        """
        return self.in_stream.readline()
