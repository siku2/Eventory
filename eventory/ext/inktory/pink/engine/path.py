from typing import Union

from .decorators import classproperty


class Component:  # TODO: Maybe implement default c# Component stuff
    index: int
    name: str

    def __init__(self, comp: Union[int, str]):
        self.index = -1
        self.name = None

        if isinstance(comp, int):
            self.index = comp
        elif isinstance(comp, str):
            self.name = comp

    def __str__(self) -> str:
        if self.is_index:
            return str(self.index)
        else:
            return self.name

    def __eq__(self, other) -> bool:
        if isinstance(other, Component):
            if other.is_index == other.is_index:
                if self.is_index:
                    return self.index == other.index
                else:
                    return self.name == other.name
            else:
                return False
        return NotImplemented

    def __hash__(self) -> int:
        if self.is_index:
            return self.index
        else:
            return hash(self.name)

    @property
    def is_index(self) -> bool:
        return self.index >= 0

    @property
    def is_parent(self) -> bool:
        return self.name == Path.parent_id

    @staticmethod
    def to_parent() -> "Component":
        return Component(Path.parent_id)


class Path:  # TODO: Maybe implement default c# path stuff
    parent_id = "^"

    def __init__(self, pri=None, sec=None):
        self._components = []
        self._components_string = None
        self.is_relative = False
        if isinstance(pri, Component) and isinstance(sec, Path):
            self._components.append(pri)
            self._components.extend(sec._components)
        elif isinstance(pri, str) and not sec:
            self.components_string = pri
        else:
            self._components.extend(pri)
            self.is_relative = bool(sec)

    def __str__(self):
        return self.components_string

    def __len__(self):
        return self.length

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, Path):
            if len(other._components) != len(self._components):
                return False
            if other.is_relative != self.is_relative:
                return False
            return other._components == self._components
        return NotImplemented

    @property
    def head(self):
        if len(self._components) > 0:
            return self._components[0]

    @property
    def tail(self):
        if len(self._components) >= 2:
            tail_comps = self._components[1:]
            return Path(tail_comps)
        else:
            return Path.self

    @property
    def length(self):
        return len(self._components)

    @property
    def last_component(self):
        last_comp_ind = len(self._components) - 1
        if last_comp_ind >= 0:
            return self._components[last_comp_ind]
        else:
            return None

    @property
    def contains_named_component(self):
        for comp in self._components:
            if not comp.is_index:
                return True
        return False

    @property
    def components_string(self):
        if not self._components_string:
            self._components_string = ".".join(map(str, self._components))
            if self.is_relative:
                self._components_string = "." + self._components_string
        return self._components_string

    @components_string.setter
    def components_string(self, value):
        self._components.clear()
        self._components_string = value
        if not self._components_string:
            return
        if self._components_string[0] == ".":
            self.is_relative = True
            self._components_string = self.components_string[1:]
        else:
            self.is_relative = False

        component_strings = self.components_string.split(".")
        for component in component_strings:
            if component.isnumeric():
                self._components.append(Component(int(component)))
            else:
                self._components.append(Component(component))

    # noinspection PyMethodParameters
    @classproperty
    def self(cls):
        path = Path()
        path.is_relative = True
        return path

    def get_component(self, index):
        return self._components[index]

    # noinspection PyProtectedMember
    def path_by_appending_path(self, path_to_append):
        p = Path()
        upward_moves = 0
        for i, comp in enumerate(path_to_append._components):
            if comp.is_parent:
                upward_moves += 1
            else:
                break
        for i in range(len(self._components) - upward_moves):
            p._components.append(self._components[i])
        for i in range(len(path_to_append._components)):
            p._components.append(path_to_append._components[i])
        return p

    def path_by_appending_component(self, c: Component) -> "Path":
        p = Path()
        p._components.extend(self._components)
        p._components.append(c)
        return p
