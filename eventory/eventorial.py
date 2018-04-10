"""This module contains the Eventorial class and its utility functions.

Attributes:
    URL_REGEX (Pattern): Regex used to check if a string is a url
    SANITISE_REGEX_STEPS (Tuple[Pattern]): Regex applied to a string in order to obtain a sanitised version of said string.
"""

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
    (re.compile(r"[ _]+"), " "),  # reduce space
    (re.compile(r"(^ +)|( +$)"), "")  # trim ends
)
_DEFAULT = object()

log = logging.getLogger(__name__)


class Eventorial:
    """An environment for Eventories.

    Args:
        directory: Directory path to store data in. If not provided the Eventorial uses a temporary directory which will be destroyed at the end.
            When provided with a path, the Eventorial loads all files that already exist in the directory.
        loop: Loop to use for various async operations. Uses asyncio.get_event_loop() if not specified.

    Attributes:
        eventories (Dict[str, Eventory]): Dictionary containing all loaded Eventories
        loop (AbstractEventLoop): Loop being used
        aiosession (ClientSession): ClientSession used for internet access
        directory (str): Path to directory used to store data
    """

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
        """Clean the Eventorial.

        Closes the ClientSession and removes the temporary directory if one has been created.
        """
        if hasattr(self, "_tempdir"):
            self._tempdir.cleanup()
            log.debug(f"{self} removed temporary directory")
        self.loop.create_task(asyncio.gather(
            self.aiosession.close(),
        ))
        log.debug("{self} cleaned up")

    def add(self, source: Union[Eventory, str, TextIOBase]):
        """Add an Eventory to this Eventorial.

        Args:
            source: Can be an Eventory to add, a string containing a serialised Eventory or an open file to load the Eventory from

        Raises:
            TODO
        """
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
        """Remove an Eventory from the Eventorial.

        Args:
            item: Eventory to removes

        Raises:
            KeyError: If the Eventory isn't part of the Eventorial
        """
        title = sanitise_string(item.title)
        self.eventories.pop(title)
        os.remove(path.join(self.directory, item.filename))

    def get(self, title: str, default: Any = _DEFAULT) -> Eventory:
        """Get an Eventory from this Eventorial.

        Args:
            title: Name of the Eventory to retrieve
            default: Default value to return if no Eventory found

        Returns:
            Eventory

        Raises:
            KeyError: If no Eventory with that title was found and default wasn't specified.
        """
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
        """Retrieve text from a source.

        Contrary to the get_data function this method doesn't assume that all strings are urls. It checks whether the string is a url using the
        URL_REGEX and if it isn't a url it treats it as the name of a file relative to the directory of the Eventorial.

        Args:
            source: Source to retrieve text from

        Returns:
            str: Retrieved text

        Raises:
            TODO
        """
        if isinstance(source, str):
            if not URL_REGEX.match(source):
                with open(path.join(self.directory, source), "r", encoding="utf-8") as f:
                    return await self.load_data(f, **kwargs)
        return await get_data(source, session=self.aiosession, **kwargs)

    async def load(self, source: Union[str, URL, TextIOBase], **kwargs) -> Eventory:
        """Load an Eventory from a source into this Eventorial.

        Contrary to the get_eventory function this method doesn't assume that all strings are urls. It checks whether the string is a url using the
        URL_REGEX and if it isn't a url it treats it as the name of a file relative to the directory of the Eventorial.

        Args:
            source: Source to load Eventory from

        Returns:
            Eventory: Eventory that was added to the Eventorial

        Raises:
            TODO
        """
        data = await self.load_data(source, **kwargs)
        eventory = load(data, **kwargs)
        self.add(eventory)
        return eventory


def sanitise_string(title: str) -> str:
    """Sanitise a string.

    Removes all non-alphanumeric characters, trims both ends of redundant spacing and replaces multiple spaces with a single one.

    Args:
        title: String to sanitise

    Returns:
        str: Sanitised string
    """
    title = title.lower()
    for regex, repl in SANITISE_REGEX_STEPS:
        title = regex.sub(repl, title)
    return title


async def get_data(source: Union[str, URL, TextIOBase], session: ClientSession = None, **kwargs) -> str:
    """Retrieve text from a source.

    Args:
        source: Source to get the text from
        session: Used to fetch online resources

    Returns:
        str: Retrieved text

    Raises:
        ValueError: When no session was provided but source was a url
        TypeError: When source isn't of the correct type
    """
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
    """Get an Eventory from a source.

    Args:
        source: Source to fetch Eventory from (open file, url)
        session: Used to fetch online resources

    Returns:
        Eventory: Eventory that was loaded from source

    Raises:
        ValueError: When no session was provided but source was a url
        TypeError: When source isn't of the correct type
    """
    data = await get_data(source, session)
    return load(data, **kwargs)
