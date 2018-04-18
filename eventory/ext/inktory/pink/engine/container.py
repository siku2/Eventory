from enum import IntFlag
from typing import Dict, Iterable, List, Optional, Union

from .named_content import NamedContent
from .object import Object
from .path import Component, Path


class CountFlags(IntFlag):
    Visits = 1
    Turns = 2
    CountStartOnly = 4


class Container(Object, NamedContent):
    _content: List[Object]
    _path_to_first_leaf_content: "Path"
    named_content: Dict[str, NamedContent]

    def __init__(self):
        super().__init__()
        self._content = []
        self._path_to_first_leaf_content = None
        self.name = ""
        self.named_content = {}
        self.visits_should_be_counted = False
        self.turn_index_should_be_counted = False
        self.counting_at_start_only = False

    @property
    def content(self) -> List[Object]:
        return self._content

    @content.setter
    def content(self, value: Object):
        self.add_content(value)

    @property
    def named_only_content(self) -> Dict[str, Object]:
        named_only_content_dict = {}
        for key, value in self.named_content.values():
            named_only_content_dict[key] = value

        c: NamedContent
        for c in self.content:
            if c and c.has_valid_name:
                named_only_content_dict.pop(c.name)

        if not named_only_content_dict:
            named_only_content_dict = None
        return named_only_content_dict

    @named_only_content.setter
    def named_only_content(self, value: Dict[str, Object]):
        existing_named_only = self.named_only_content
        if existing_named_only:
            for key, val in existing_named_only.items():
                self.named_content.pop(key)
        if not value:
            return
        for key, val in value:
            if val:
                self.add_to_named_content_only(val)

    @property
    def count_flags(self) -> int:
        flags = 0
        if self.visits_should_be_counted:
            flags |= CountFlags.Visits
        if self.turn_index_should_be_counted:
            flags |= CountFlags.Turns
        if self.counting_at_start_only:
            flags |= CountFlags.CountStartOnly

        if flags == CountFlags.CountStartOnly:
            flags = 0
        return flags

    @count_flags.setter
    def count_flags(self, value: int):
        flag = CountFlags(value)
        if flag & CountFlags.Visits > 0:
            self.visits_should_be_counted = True
        if flag & CountFlags.Turns > 0:
            self.turn_index_should_be_counted = True
        if flag & CountFlags.CountStartOnly > 0:
            self.counting_at_start_only = True

    @property
    def has_valid_name(self) -> bool:
        return bool(self.name)

    @property
    def path_to_first_leaf_content(self) -> "Path":
        if not self._path_to_first_leaf_content:
            self._path_to_first_leaf_content = self.path.path_by_appending_path(self.internal_path_to_first_leaf_content)
        return self._path_to_first_leaf_content

    @property
    def internal_path_to_first_leaf_content(self) -> "Path":
        components = []
        container = self
        while container:
            if len(container.content) > 0:
                components.append(Component(0))
                container = container.content[0]
        return Path(components)

    def add_content(self, content_obj: Union[Object, Iterable[Object]]):
        if isinstance(content_obj, Iterable):
            for content in content_obj:
                self.add_content(content)
        self.content.append(content_obj)
        if content_obj.parent:
            raise ValueError("Content is already in " + str(content_obj.parent))
        content_obj.parent = self
        self.try_add_named_content(content_obj)

    def insert_content(self, content_obj: Object, index: int):
        self.content.insert(index, content_obj)
        if content_obj.parent:
            raise ValueError("Content is already in " + str(content_obj.parent))
        content_obj.parent = self
        self.try_add_named_content(content_obj)

    def try_add_named_content(self, content_obj: Object):
        if isinstance(content_obj, NamedContent) and content_obj.has_valid_name:
            self.add_to_named_content_only(content_obj)

    def add_to_named_content_only(self, named_content_obj: NamedContent):
        assert (isinstance(named_content_obj, Object) and isinstance(named_content_obj, NamedContent)), "Can only add Objects to a Container"
        named_content_obj.parent = self
        self.named_content[named_content_obj.name] = named_content_obj

    def add_contents_of_container(self, other_container: "Container"):
        self.content.extend(other_container.content)
        for obj in other_container.content:
            obj.parent = self
            self.try_add_named_content(obj)

    def content_with_path_component(self, component: Component) -> Optional[Object]:
        if component.is_index:
            if 0 < component.index < len(self.content):
                return self.content[component.index]
            else:
                return None
        elif component.is_parent:
            return self.parent
        else:
            found_content: Object = self.named_content.get(component.name)
            if found_content:
                return found_content
            else:
                raise StoryException("Content \"" + component.name + "\" not found at path: \"" + self.path + "\"")

    def content_at_path(self, path: Path, partial_path_length: int = -1) -> Object:
        if partial_path_length == -1:
            partial_path_length = path.length

        current_container = self
        current_obj = self
        for i in range(partial_path_length):
            comp = path.get_component(i)
            if not current_container:
                raise Exception("Path continued, but previous object wasn't a container: " + str(current_obj))
            current_obj = current_container.content_with_path_component(comp)
            current_container = current_obj
        return current_obj

    def build_string_of_hierarchy(self, indentation: int = 0, pointed_obj: Object = None) -> str:
        sb = ""

        def append_indentation():
            nonlocal sb, indentation
            sb += 4 * indentation * " "

        append_indentation()
        sb += "["
        if self.has_valid_name:
            sb += f" ({self.name})"
        if self == pointed_obj:
            sb += "  <---"

        sb += "\n"
        indentation += 1
        for i, obj in enumerate(self.content):
            if isinstance(obj, Container):
                sb = obj.build_string_of_hierarchy(indentation, pointed_obj)
            else:
                append_indentation()
                if isinstance(obj, str):
                    formatted_obj = str(obj).replace("\n", "\\n")
                    sb += f"\"{formatted_obj}\""
                else:
                    sb += str(obj)
            if i != len(self.content) - 1:
                sb += ","

            if not isinstance(obj, Container) and obj == pointed_obj:
                sb += "  <---"
            sb += "\n"
        only_named = {}
        for key, value in self.named_content.items():
            if value in self.content:
                continue
            else:
                only_named[key] = value
        if len(only_named) > 0:
            append_indentation()
            sb += "-- named: --\n"
            for key, value in only_named.items():
                assert isinstance(value, Container), "Can only print out named Containers"
                sb = value.build_string_of_hierarchy(indentation, pointed_obj)
                sb += "\n"
        indentation -= 1
        append_indentation()
        sb += "]"
        return sb
