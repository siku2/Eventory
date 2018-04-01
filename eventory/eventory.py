"""
I call it eventory because it's an event story. Geddit? Genius, right? I know.
.evory files
something something by me.
"""

from typing import Any, Sequence, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .parser import Eventoriment
    from .instructor import Eventructor
    from .narrator import Eventarrator


class EventoryMeta:
    def __init__(self, title: str, description: str, version: int, author: str, requirements: Sequence["Eventoriment"]):
        self.title = title
        self.description = description
        self.version = version
        self.author = author

        self.requirements = requirements

    def __repr__(self) -> str:
        return f"\"{self.title}\" - {self.author} ({self.version})"


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

    def __getattr__(self, item):
        return getattr(self.meta, item)

    def narrate(self, eventarrator: "Eventarrator", **kwargs) -> "Eventructor":
        return self.eventructor_cls(self, eventarrator, **kwargs)
