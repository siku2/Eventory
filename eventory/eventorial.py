import asyncio
import atexit
import re
from io import TextIOBase
from os import path
from tempfile import TemporaryDirectory
from typing import Any, Union

from aiohttp import ClientSession
from yarl import URL

from .eventory import Eventory
from .parser import load

URL_REGEX = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
_DEFAULT = object()


class Eventorial:
    """Another absolutely genius name for the Eventory manager... Don't you think?"""

    def __init__(self, directory: str = None, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.aiosession = ClientSession(loop=self.loop)
        if directory:
            self.directory = directory
        else:
            self._tempdir = TemporaryDirectory(prefix="Eventory_")
            self.directory = self._tempdir.name

        self.eventories = []

        atexit.register(self.cleanup)

    def __str__(self):
        return f"<Eventorial {len(self.eventories)} Eventory/ies loaded>"

    def __len__(self):
        return len(self.eventories)

    def __del__(self):
        self.cleanup()

    def __contains__(self, item):
        return item in self.eventories

    def __delitem__(self, key):
        return self.remove(key)

    def __getitem__(self, item):
        return self.get(item)

    def __iter__(self):
        return iter(self.eventories)

    def cleanup(self):
        if hasattr(self, "_tempdir"):
            self._tempdir.cleanup()
        loop = self.loop if not self.loop.is_closed() else asyncio.get_event_loop()
        loop.run_until_complete(self.aiosession.close())

    def add(self, source: Union[Eventory, str, TextIOBase]):
        if isinstance(source, Eventory):
            eventory = source
        else:
            eventory = load(source)
        self.eventories.append(eventory)

    def remove(self, item: Eventory):
        pass

    def get(self, title: str, default: Any = _DEFAULT) -> Eventory:

        story = next((eventory for eventory in self.eventories if eventory.title == title), None)
        if story is None:
            if default is _DEFAULT:
                raise ValueError(f"No Eventory with title \"{title}\"")
            else:
                return default
        else:
            return story

    async def load(self, source: Union[str, URL, TextIOBase], **kwargs) -> Eventory:
        if isinstance(source, str):
            if not URL_REGEX.match(source):
                with open(path.join(self.directory, source), "r") as f:
                    return await self.load(f, **kwargs)
        eventory = await get_eventory(source, session=self.aiosession, **kwargs)
        self.add(eventory)
        return eventory


async def get_eventory(source: Union[str, URL, TextIOBase], session: ClientSession = None, **kwargs) -> Eventory:
    if isinstance(source, (str, URL)):
        if session is None or not isinstance(session, ClientSession):
            raise ValueError(f"You need to pass a {ClientSession} in order to download Eventories")
        async with session.get(source) as resp:
            data = await resp.text()
    elif isinstance(source, TextIOBase):
        data = source.read()
    else:
        raise TypeError(f"Make sure to pass the correct type. ({type(source)} is invalid!)")
    return load(data, **kwargs)
