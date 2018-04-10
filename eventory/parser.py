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
    aliases = set(aliases)
    aliases.add(cls.__name__)
    PARSER_MAP.append((cls, aliases))
    log.info(f"registered parser {cls} to handle {aliases}")


def find_parser(targets: Union[str, Sequence[str]], default=_DEFAULT) -> "EventoryParser":
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
    """The puns are hitting hard. Dis a requirement for an Eventory"""

    def __init__(self, package: str, source: str = None):
        self.package = package
        self.source = source or package

    def __repr__(self) -> str:
        return f"<Eventoriment \"{self.package}\""

    def to_dict(self) -> Union[str, Dict[str, Any]]:
        if self.package is not self.source:
            return vars(self)
        else:
            return self.package

    def get(self) -> ModuleType:
        try:
            return importlib.import_module(self.package)
        except ModuleNotFoundError:
            log.debug(f"{self} not installed, installing...")
            subprocess.run(["pip", "install", self.source], check=True)
            log.debug(f"installed {self}!")
            return importlib.import_module(self.package)


class EventoryParser(metaclass=abc.ABCMeta):
    instructor = Eventructor

    @classmethod
    def split(cls, text: str) -> Tuple[str, str]:
        values = HEAD_DELIMITER.split(text, 2)
        if len(values) == 3:
            head, content = values[1:3]
        elif len(values) == 2:
            head, content = values
        else:
            raise MalformattedEventory("Can't split into head and content parts!", text)
        return head, content

    def extend_meta(self, meta: Mapping) -> dict:
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
        raise NotImplementedError

    @classmethod
    def preload(cls, stream: Union[str, TextIOBase]) -> Tuple[str, str]:
        if isinstance(stream, TextIOBase):
            data = stream.read()
        else:
            data = stream
        return cls.split(data)

    def load(self, stream: Union[str, TextIOBase], instructor: Type[Eventructor] = None) -> Eventory:
        head, content = self.preload(stream)
        meta, kwargs = self.parse_head(head)
        content = self.parse_content(content)
        return Eventory(meta, content, instructor or self.instructor, **kwargs)


def load_data(stream: Union[str, TextIOBase]) -> str:
    if isinstance(stream, TextIOBase):
        data = stream.read()
    else:
        data = stream
    return data


def load(stream: Union[str, TextIOBase], *, parser: Type[EventoryParser] = None, instructor: Type[Eventructor] = None, **kwargs) -> Eventory:
    data = load_data(stream)

    if not parser:
        head, content = EventoryParser.preload(data)
        head = yaml.load(head)
        parser = find_parser(head.get("parser"))

    return parser(**kwargs).load(data, instructor)
