import asyncio
import logging
import os
import re
from io import TextIOBase
from os import path
from tempfile import TemporaryDirectory
from typing import Any, Union

from aiohttp import ClientSession
from yarl import URL

from . import constants
from .eventory import Eventory
from .exceptions import EventoryAlreadyLoaded
from .parser import load

URL_REGEX = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
SANITISE_REGEX_STEPS = (
    (re.compile(r"[^a-z0-9_ ]+"), ""),  # remove unwanted chars
    (re.compile(r"(^ +)|( +$)"), ""),  # trim ends
    (re.compile(r"[ _]+"), " ")  # reduce space
)
_DEFAULT = object()

log = logging.getLogger(__name__)


class Eventorial:
    """Another absolutely genius name for the Eventory manager... Don't you think?"""

    def __init__(self, directory: str = None, *, loop=None):
        self.eventories = {}

        self.loop = loop or asyncio.get_event_loop()
        self.aiosession = ClientSession(loop=self.loop)

        if directory:
            self.directory = directory
            self._load_directory()
        else:
            self._tempdir = TemporaryDirectory(prefix="Eventory_")
            self.directory = self._tempdir.name
            log.debug(f"{self} created temporary directory in {self.directory}")

    def __str__(self):
        return f"<Eventorial {len(self.eventories)} Eventory/ies loaded>"

    def __len__(self):
        return len(self.eventories)

    def __del__(self):
        self.cleanup()

    def __contains__(self, item):
        return (item in self.eventories.keys()) or bool(self.get(item))

    def __delitem__(self, key):
        return self.remove(key)

    def __getitem__(self, item):
        return self.get(item)

    def __iter__(self):
        return iter(self.eventories)

    def _load_directory(self):
        names = os.listdir(self.directory)
        loaded_eventories = 0
        for name in names:
            if name.endswith(constants.FILE_SUFFIX):
                with open(path.join(self.directory, name), "r") as f:
                    self.add(load(f))
                    loaded_eventories += 1
        log.info(f"{self} loaded {loaded_eventories} Eventory/ies from directory")

    def cleanup(self):
        if hasattr(self, "_tempdir"):
            self._tempdir.cleanup()
            log.debug(f"{self} removed temporary directory")
        self.loop.create_task(asyncio.gather(
            self.aiosession.close(),
        ))
        log.debug("{self} cleaned up")

    def add(self, source: Union[Eventory, str, TextIOBase]):
        if isinstance(source, Eventory):
            eventory = source
        else:
            eventory = load(source)
        sane_title = sanitise_string(eventory.title)
        if sane_title in self.eventories:
            raise EventoryAlreadyLoaded(eventory.title)
        self.eventories[sane_title] = eventory
        eventory.save(path.join(self.directory, "{filename}"))

    def remove(self, item: Eventory):
        title = sanitise_string(item.title)
        self.eventories.pop(title)
        os.remove(path.join(self.directory, item.filename))

    def get(self, title: str, default: Any = _DEFAULT) -> Eventory:
        sane_title = sanitise_string(title)
        story = self.eventories.get(sane_title)
        if story is None:
            if default is _DEFAULT:
                raise KeyError(f"No Eventory with title \"{title}\"")
            else:
                return default
        else:
            return story

    async def load_data(self, source: Union[str, URL, TextIOBase], **kwargs) -> str:
        if isinstance(source, str):
            if not URL_REGEX.match(source):
                with open(path.join(self.directory, source), "r", encoding="utf-8") as f:
                    return await self.load_data(f, **kwargs)
        return await get_data(source, session=self.aiosession, **kwargs)

    async def load(self, source: Union[str, URL, TextIOBase], **kwargs) -> Eventory:
        data = await self.load_data(source, **kwargs)
        eventory = load(data, **kwargs)
        self.add(eventory)
        return eventory


def sanitise_string(title: str) -> str:
    title = title.lower()
    for regex, repl in SANITISE_REGEX_STEPS:
        title = regex.sub(repl, title)
    return title


async def get_data(source: Union[str, URL, TextIOBase], session: ClientSession = None, **kwargs) -> str:
    if isinstance(source, (str, URL)):
        if session is None or not isinstance(session, ClientSession):
            raise ValueError(f"You need to pass a {ClientSession} in order to download Eventories")
        async with session.get(source) as resp:
            data = await resp.text()
    elif isinstance(source, TextIOBase):
        data = source.read()
    else:
        raise TypeError(f"Make sure to pass the correct type. ({type(source)} is invalid!)")
    return data


async def get_eventory(source: Union[str, URL, TextIOBase], session: ClientSession = None, **kwargs) -> Eventory:
    data = await get_data(source, session)
    return load(data, **kwargs)
