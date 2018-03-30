"""
I call it eventory because it's an event story. Geddit? Genius, right? I know.
.evory files
something something by me.
"""

from typing import Sequence, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from .parser import Eventoriment
    from .instructor import Eventructor


class EventoryHead:
    def __init__(self, title: str, description: str, version: int, author: str):
        self.title = title
        self.description = description
        self.version = version
        self.author = author


class Eventory:
    """An Eventory story"""

    def __init__(self, head: EventoryHead, content, pyrequirements: Sequence["Eventoriment"], eventructor: Type["Eventructor"], *,
                 store: dict = None, global_store: dict = None):
        self.head = head
        self.pyrequirements = pyrequirements

        self.content = content
        self.eventructor = eventructor

        self.store = store or {}
        self.global_store = global_store or {}

    def __getattr__(self, item):
        return getattr(self.head, item)
