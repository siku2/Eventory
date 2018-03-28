"""
I call it eventory because it's an event story. Geddit? Genius, right? I know.
.evory files
something something by me.
"""

import abc
import asyncio
import importlib
from asyncio import AbstractEventLoop
from concurrent.futures import Executor, ThreadPoolExecutor
from io import IOBase
from types import ModuleType
from typing import Mapping, Sequence, Type, Union

import pip
import yaml


class EventoryException(Exception):
    pass


class EventoryParserError(EventoryException):
    pass


class EventoryParserKeyError(EventoryException, KeyError):
    def __init__(self, key: str):
        self.key = key


class Eventoriment:
    """The puns are hitting hard. Dis a requirement for an Eventory"""

    def __init__(self, package: str):
        self.package = package

    def get(self) -> ModuleType:
        try:
            return importlib.import_module(self.package)
        except ImportError:
            pip.main(["install", self.package])
            return importlib.import_module(self.package)


class Eventory(metaclass=abc.ABCMeta):
    """An Eventory story"""

    def __init__(self, title: str, description: str, version: int, author: str, pyrequirements: Sequence[Eventoriment], instructions: Sequence, *,
                 store: dict = None, executor: Executor = None, loop: AbstractEventLoop = None):
        self.title = title
        self.description = description
        self.version = version
        self.author = author
        self.pyrequirements = pyrequirements

        self.instructions = instructions

        self.store = store or {}

        self.loop = loop or asyncio.get_event_loop()
        self.executor = executor or ThreadPoolExecutor(3, f"Eventory \"{title}\"")

    async def ensure_requirements(self):
        tasks = []
        for requirement in self.pyrequirements:
            task = asyncio.ensure_future(self.executor.submit(requirement.get))
            tasks.append(task)
        modules = await asyncio.gather(*tasks, loop=self.loop)
        for module in modules:
            self.store[module.__name__] = module

    @abc.abstractmethod
    async def get_input(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def output(self, out):
        raise NotImplementedError


class EventoryParser:
    def parse_meta(self, meta: Mapping) -> dict:
        try:
            data = {
                "title": meta["title"],
                "description": meta.get("description", None),
                "version": int(meta.get("version", 1)),
                "author": meta.get("author", None),
                "pyrequirements": meta.get("pyrequirements", [])
            }
        except KeyError as e:
            raise EventoryParserKeyError
        except ValueError:
            pass
        else:
            return data

    def load(self, stream: Union[str, IOBase], cls: Type[Eventory] = Eventory) -> Eventory:
        data = yaml.load(stream)
        return cls(**data)


class Eventorial:
    """Another absolutely genius name for the Eventory manager... Don't you think?"""

    def __init__(self, *, eventory: Type[Eventory] = Eventory, parser: Type[EventoryParser] = EventoryParser):
        self.eventory = eventory
        self.parser = parser
