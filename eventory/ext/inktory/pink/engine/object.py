from typing import Optional, TYPE_CHECKING

from .path import Component, Path

if TYPE_CHECKING:
    from .debug_metadata import DebugMetadata
    from .container import Container
    from .search_result import SearchResult


class Object:
    _path: Path
    parent: "Object"
    _debug_metadata: "DebugMetadata"

    def __init__(self):
        self._path = None
        self._debug_metadata = None
        self.parent = None

    def __eq__(self, other) -> bool:
        return self is other

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __bool__(self) -> bool:
        return self is not None

    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def debug_metadata(self) -> "DebugMetadata":
        if not self._debug_metadata:
            if self.parent:
                return self.parent.debug_metadata
        return self._debug_metadata

    @debug_metadata.setter
    def debug_metadata(self, value: "DebugMetadata"):
        self._debug_metadata = value

    @property
    def own_debug_metadata(self) -> "DebugMetadata":
        return self._debug_metadata

    @property
    def path(self) -> Path:
        if not self._path:
            if not self.parent:
                self._path = Path()
            else:
                comps = []
                child = self
                container = child.parent
                while container:
                    named_child = child
                    if named_child and named_child.has_valid_name:
                        comps.append(Component(named_child.name))
                    else:
                        comps.append(Component(container.content.index(child)))
                    child = container
                    container = container.parent
                self._path = Path(comps)
        return self._path

    @property
    def root_content_container(self) -> "Container":
        ancestor = self
        while ancestor.parent:
            ancestor = ancestor.parent
        return ancestor

    def debug_line_number_of_path(self, path: Path) -> Optional[int]:
        if not path:
            return None
        root = self.root_content_container
        if root:
            target_content = None
            try:
                target_content = root.content_at_path(path)
            finally:
                if target_content:
                    dm = target_content.debug_metadata
                    if dm:
                        return dm.start_line_number

    def resolve_path(self, path: Path) -> "SearchResult":
        if path.is_relative:
            nearest_container = self if isinstance(self, Container) else None
            if not nearest_container:
                assert self.parent, "Can't resolve relative path because we don't have a parent"
                nearest_container = self.parent
                assert nearest_container, "Expected parent to be a container"
                assert path.get_component(0).is_parent
                path = path.tail
            return nearest_container.content_at_path(path)
        else:
            return self.root_content_container.content_at_path(path)

    def convert_path_to_relative(self, global_path: Path) -> Path:
        own_path = self.path
        min_path_length = min(len(global_path), len(own_path))
        last_shared_path_comp_index = -1
        for i in range(min_path_length):
            own_comp = own_path.get_component(i)
            other_comp = global_path.get_component(i)

            if own_comp == other_comp:
                last_shared_path_comp_index = i
            else:
                break
        if last_shared_path_comp_index == -1:
            return global_path

        num_upwards_moves = (len(own_path) - 1) - last_shared_path_comp_index
        new_path_comps = []
        for up in range(num_upwards_moves):
            new_path_comps.append(Component.to_parent())
        for down in range(last_shared_path_comp_index + 1, len(global_path)):
            new_path_comps.append(global_path.get_component(down))
        relative_path = Path(new_path_comps, True)
        return relative_path

    def compact_path_string(self, other_path: Path) -> str:
        if other_path.is_relative:
            relative_path_str = other_path.components_string
            global_path_str = self.path.path_by_appending_path(other_path).components_string
        else:
            relative_path = self.convert_path_to_relative(other_path)
            relative_path_str = relative_path.components_string
            global_path_str = other_path.components_string
        if len(relative_path_str) < len(global_path_str):
            return relative_path_str
        else:
            return global_path_str

    def copy(self) -> "Object":
        raise NotImplementedError(str(type(self)) + " doesn't support copying")

    def set_child(self, obj: "Object", value: "Object"):
        if obj:
            obj.parent = None
        obj = value
        if obj:
            obj.parent = self
