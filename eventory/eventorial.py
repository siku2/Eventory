from typing import Type

from .eventory import Eventory
from .parser import EventoryParser


class Eventorial:
    """Another absolutely genius name for the Eventory manager... Don't you think?"""

    def __init__(self, *, eventory: Type[Eventory] = Eventory, parser: Type[EventoryParser] = EventoryParser):
        self.eventory = eventory
        self.parser = parser

    def load(self, source: str):
        pass
