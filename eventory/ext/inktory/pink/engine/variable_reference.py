from typing import TYPE_CHECKING

from .object import Object
from .path import Path

if TYPE_CHECKING:
    from .container import Container


class VariableReference(Object):
    name: str
    path_for_count: Path

    def __init__(self, name: str = None):
        super().__init__()
        self.name = name
        self.path_for_count = None

    def __str__(self) -> str:
        if self.name:
            return f"var({self.name})"
        else:
            path_str = self.path_string_for_count
            return f"read_count({path_str})"

    @property
    def container_for_count(self) -> "Container":
        return self.resolve_path(self.path_for_count).container

    @property
    def path_string_for_count(self) -> str:
        return self.compact_path_string(self.path_for_count) if self.path_for_count else None

    @path_string_for_count.setter
    def path_string_for_count(self, value: str):
        if not value:
            self.path_for_count = None
        else:
            self.path_for_count = Path(value)
