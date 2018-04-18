from typing import Optional, TYPE_CHECKING

from .container import Container

if TYPE_CHECKING:
    from .object import Object


class SearchResult:
    obj: "Object"
    approximate: bool

    @property
    def correct_obj(self) -> "Object":
        return None if self.approximate else self.obj

    @property
    def container(self) -> Optional[Container]:
        return self.obj if isinstance(self.obj, Container) else None
