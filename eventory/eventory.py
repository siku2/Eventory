"""
I call it eventory because it's an event story. Geddit? Genius, right? I know.
.evory files
something something by me.
"""

import re
from io import TextIOBase
from typing import Any, Dict, Sequence, TYPE_CHECKING, Type, Union

import yaml

from . import constants

if TYPE_CHECKING:
    from .parser import Eventoriment
    from .instructor import Eventructor
    from .narrator import Eventarrator

FILENAME_REGEX = re.compile(r"[\W_]+")


class EventoryMeta:
    def __init__(self, title: str, description: str, version: int, author: str, requirements: Sequence["Eventoriment"]):
        self.title = title
        self.description = description
        self.version = version
        self.author = author

        self.requirements = requirements

    def __repr__(self) -> str:
        return f"\"{self.title}\" - {self.author} ({self.version})"

    def to_dict(self) -> Dict[str, Any]:
        data = vars(self)
        data["requirements"] = [req.to_dict() for req in data["requirements"]]
        return data

    def serialise(self) -> str:
        return yaml.dump(self.to_dict())


class Eventory:
    """An Eventory story"""

    def __init__(self, meta: EventoryMeta, content: Any, eventructor_cls: Type["Eventructor"], *, store: dict = None, global_store: dict = None):
        self.meta = meta
        self.content = content
        self.eventructor_cls = eventructor_cls

        self.store = store or {}
        self.global_store = global_store or {}

    def __repr__(self) -> str:
        return f"{self.meta}: {self.eventructor_cls}"

    def __getattr__(self, item) -> Any:
        return getattr(self.meta, item)

    @property
    def filename(self):
        title = FILENAME_REGEX.sub("_", self.title.lower())
        return f"{title}{constants.FILE_SUFFIX}"

    def narrate(self, eventarrator: "Eventarrator", **kwargs) -> "Eventructor":
        return self.eventructor_cls(self, eventarrator, **kwargs)

    def serialise(self) -> str:
        head = self.meta.serialise()
        content = self.eventructor_cls.serialise_content(self.content)
        return f"---\n{head}\n---\n\n{content}"

    def save(self, fp: Union[str, TextIOBase] = None) -> TextIOBase:
        if not fp:
            fp = self.filename

        if isinstance(fp, str):
            fp = fp.format(filename=self.filename)
            with open(fp, "w+", encoding="utf-8") as f:
                return self.save(f)

        data = self.serialise()
        fp.write(data)
        return fp
