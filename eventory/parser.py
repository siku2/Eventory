import abc
import importlib
import re
from io import TextIOBase
from types import ModuleType
from typing import Any, Mapping, Tuple, Union

import pip
import yaml

from .eventory import Eventory, EventoryHead
from .exceptions import EventoryParserKeyError, EventoryParserValueError
from .instructor import Eventructor


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


class EventoryParser(metaclass=abc.ABCMeta):
    EVENTRUCTOR = Eventructor
    HEAD_BOUNDARY = re.compile(r"^-{3,}$", re.MULTILINE)

    def split(self, text: str) -> Tuple[str, str]:
        _, head, content = self.HEAD_BOUNDARY.split(text, 2)
        return head, content

    def extend_meta(self, meta: Mapping) -> dict:
        try:
            data = {
                "title": meta["title"],
                "description": meta.get("description", None),
                "author": meta.get("author", None),
                "version": int(meta.get("version", 1)),
                "parser": meta.get("parser", None),
                "pyrequirements": meta.get("pyrequirements", [])
            }
        except KeyError as e:
            raise EventoryParserKeyError(e.args[0])
        except ValueError:
            raise EventoryParserValueError("version", meta["version"])
        else:
            return data

    def parse_head(self, head: Union[str, Mapping]) -> EventoryHead:
        if isinstance(head, str):
            head = yaml.load(head)
        meta = self.extend_meta(head["meta"])
        return EventoryHead(**meta)

    @abc.abstractmethod
    def parse_content(self, content: Any) -> Any:
        pass

    def load(self, stream: Union[str, TextIOBase]) -> Eventory:
        if isinstance(stream, TextIOBase):
            data = stream.read()
        else:
            data = stream
        head, content = self.split(data)
        head = self.parse_head(head)
        content = self.parse_content(content)
        return Eventory(head, content, self.EVENTRUCTOR)
