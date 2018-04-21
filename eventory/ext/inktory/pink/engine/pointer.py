from typing import Optional

from .container import Container
from .object import Object
from .path import Component, Path


class Pointer:
    Null: "Pointer"

    container: Container
    index: int

    def __init__(self, container: Optional[Container], index: int):
        self.container = container
        self.index = index

    @property
    def is_null(self) -> bool:
        return self.container is None

    @property
    def path(self) -> Optional[Path]:
        if self.is_null:
            return None

        if self.index >= 0:
            return self.container.path.path_by_appending_component(Component(self.index))
        else:
            return self.container.path

    def resolve(self) -> Optional[Object]:
        if self.index < 0:
            return self.container
        if self.container is None:
            return None
        if len(self.container.content) == 0:
            return self.container
        if self.index >= len(self.container.content):
            return None
        return self.container.content[self.index]

    @staticmethod
    def start_of(container: Container) -> "Pointer":
        return Pointer(container, 0)


Pointer.Null = Pointer(None, -1)
