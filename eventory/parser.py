"""This module contains one of the most important things of Eventory. The Parser.

Attributes:
    HEAD_DELIMITER (Pattern): Regex to separate head from content
    PARSER_MAP (List[Tuple[Type[EventoryParser], Sequence[str]]]: A list of tuples of parsers and their aliases used by the find_parser function.
"""

import abc
import importlib
import logging
import re
import subprocess
from io import TextIOBase
from types import ModuleType
from typing import Any, Dict, Mapping, Sequence, Tuple, Type, Union

import yaml

from .eventory import Eventory, EventoryMeta
from .exceptions import EventoryNoParserFound, EventoryParserHeadError, EventoryParserKeyError, EventoryParserValueError, MalformattedEventory
from .instructor import Eventructor

_DEFAULT = object()
HEAD_DELIMITER = re.compile(r"^-{3,}$", re.MULTILINE)
PARSER_MAP = []

log = logging.getLogger(__name__)


def register_parser(cls: Type["EventoryParser"], aliases: Sequence[str]):
    """Register a parser and its corresponding aliases so it can be used when loading Eventories.

    This function should only really be called when you're developing your own parsers.

    Args:
        cls: Class of the Parser
        aliases: List of aliases the parser may be referred to
    """
    aliases = set(aliases)
    aliases.add(cls.__name__)
    PARSER_MAP.append((cls, aliases))
    log.info(f"registered parser {cls} to handle {aliases}")


def find_parser(targets: Union[str, Sequence[str]], default=_DEFAULT) -> "EventoryParser":
    """Find a parser based on its name.

    Args:
        targets: Name(s) to look for. If a Sequence is provided, iterate through the Sequence and return the first valid EventoryParser.
        default: Default value to return if no EventoryParser found.

    Returns:
        EventoryParser: Parser class corresponding to the name.

    Raises:
        EventoryNoParserFound: If no parser could be found for the provided target(s)
    """
    if isinstance(targets, str):
        targets = [targets]
    for target in targets:
        cls = next((cls for cls, aliases in PARSER_MAP if target in aliases), None)
        if cls is not None:
            log.debug(f"chose parser {cls} for target {targets}")
            return cls
    if default is _DEFAULT:
        raise EventoryNoParserFound(f"Couldn't find a parser for \"{targets}\"")


class Eventoriment:
    """Wraps a requirement for an Eventory.

    Args:
        package: Name of the package to install. This is later used to import the package.
        source: Source to pass to "pip install". If not specified this is the same as package.

    Attributes:
        package: Name of the package to install. This is later used to import the package.
        source: Source to pass to "pip install". If not specified this is the same as package.
    """

    def __init__(self, package: str, source: str = None):
        self.package = package
        self.source = source or package

    def __repr__(self) -> str:
        return f"<Eventoriment \"{self.package}\""

    def to_dict(self) -> Union[str, Dict[str, Any]]:
        """Get a dictionary representation for this Eventoriment.

        Returns:
            Union[str, Dict[str, Any]]: If the source is the same as the package it just returns the package, otherwise it returns both.
        """
        if self.package is not self.source:
            return vars(self)
        else:
            return self.package

    def get(self) -> ModuleType:
        """Get this module.

        If it's not already installed, the package is installed using pip.

        Returns:
            ModuleType: The module specified
        """
        try:
            return importlib.import_module(self.package)
        except ModuleNotFoundError:
            log.debug(f"{self} not installed, installing...")
            subprocess.run(["pip", "install", self.source], check=True)
            log.debug(f"installed {self}!")
            return importlib.import_module(self.package)


class EventoryParser(metaclass=abc.ABCMeta):
    """The EventoryParser parses data into an Eventory.

    Attributes:
        instructor: Eventructor to use for Eventories parsed by this EventoryParser
    """
    instructor = Eventructor

    @classmethod
    def split(cls, text: str) -> Tuple[str, str]:
        """Split text into head and content parts.

        Args:
            text: Text to split

        Raises:
            MalformattedEventory: When the data can't be split into head and content
        """
        values = HEAD_DELIMITER.split(text, 2)
        if len(values) == 3:
            head, content = values[1:3]
        elif len(values) == 2:
            head, content = values
        else:
            raise MalformattedEventory("Can't split into head and content parts!", text)
        return head, content

    def extend_meta(self, meta: Mapping) -> dict:
        """Extend a raw meta to include all required keys.

        Args:
            meta: Incomplete meta to complete

        Returns:
            dict: Meta containing all necessary keys

        Raises:
            EventoryParserKeyError: When there's a key missing
            EventoryParserValueError: When the value of a key isn't valid
        """
        try:
            data = {
                "title": meta["title"],
                "description": meta.get("description", None),
                "author": meta.get("author", None),
                "version": int(meta.get("version", 1)),
                "requirements": [Eventoriment(requirement) for requirement in meta.get("requirements", [])]
            }
        except KeyError as e:
            raise EventoryParserKeyError(e.args[0])
        except ValueError:
            raise EventoryParserValueError("version", meta["version"])
        else:
            return data

    def parse_head(self, head: str) -> Tuple[EventoryMeta, dict]:
        """Parse the raw head of an Eventory file.

        Args:
            head: Head part of the

        Returns:
            Tuple[EventoryMeta, dict]:

        Raises:
            EventoryParserHeadError: When the head couldn't be parsed as YAML
            EventoryParserKeyError: When the head doesn't contain a meta tag
            EventoryParserValueError: When the meta key doesn't contain the correct value
        """
        try:
            head = yaml.load(head)
        except yaml.YAMLError as e:
            raise EventoryParserHeadError("Couldn't parse Eventory head!") from e

        raw_meta = head.get("meta")
        if not raw_meta:
            raise EventoryParserKeyError("meta")
        elif not isinstance(raw_meta, Mapping):
            raise EventoryParserValueError("meta", raw_meta, "Meta needs to be an Object!")

        meta = EventoryMeta(**self.extend_meta(raw_meta))
        store = head.get("store")
        global_store = head.get("global_store")
        return meta, dict(store=store, global_store=global_store)

    @staticmethod
    @abc.abstractmethod
    def parse_content(content: Any) -> Any:
        """Parse the raw content into a form usable by the Eventructor."""
        raise NotImplementedError

    @classmethod
    def preload(cls, stream: Union[str, TextIOBase]) -> Tuple[str, str]:
        """Read data from stream and split into head, content.

        This is just a wrapper around split.

        Args:
            stream: Stream to read data from

        Returns:
            Tuple[str, str]: Head and content separated.

        Raises:
            TODO
        """
        if isinstance(stream, TextIOBase):
            data = stream.read()
        else:
            data = stream
        return cls.split(data)

    def load(self, stream: Union[str, TextIOBase], instructor: Type[Eventructor] = None) -> Eventory:
        """Load data from the stream and parse it into an Eventory.

        Args:
            stream: Stream to load from
            instructor: Override the default instructor chosen by the EventoryParser

        Returns:
            Eventory: Final Eventory

        Raises:
            TODO
        """
        head, content = self.preload(stream)
        meta, kwargs = self.parse_head(head)
        content = self.parse_content(content)
        return Eventory(meta, content, instructor or self.instructor, **kwargs)


def load_data(stream: Union[str, TextIOBase]) -> str:
    """Load text from a stream.

    Args:
        stream: Stream to take text from

    Returns:
        str: Loaded text

    Raises:
        TODO
    """
    if isinstance(stream, TextIOBase):
        data = stream.read()
    else:
        data = stream
    return data


def load(stream: Union[str, TextIOBase], *, parser: Type[EventoryParser] = None, instructor: Type[Eventructor] = None, **kwargs) -> Eventory:
    """Loads an Eventory from a stream.

    Args:
        stream: Stream to read from
        parser: Override the parser used to parse the data. If not provided the function tries to determine the correct parser based on the head of
            the Eventory.
        instructor: Specify to override the instructor specified by the parser

    Returns:
        Eventory: Eventory loaded from the stream

    Raises:
        TODO
    """
    data = load_data(stream)

    if not parser:
        head, content = EventoryParser.preload(data)
        head = yaml.load(head)
        parser = find_parser(head.get("parser"))

    return parser(**kwargs).load(data, instructor)
