from collections import UserDict
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, Union

from .decorators import classproperty

if TYPE_CHECKING:
    from .story import Story
    from .list_definition import ListDefinition


class InkListItem:
    origin_name: str
    item_name: str

    def __init__(self, *args):
        if len(args) == 2:
            self.origin_name, self.item_name = args
        elif len(args) == 1:
            name_parts = args[0].split(".")
            self.origin_name, self.item_name = name_parts
        else:
            raise ValueError

    def __str__(self) -> str:
        return self.full_name

    def __eq__(self, other) -> bool:
        if isinstance(other, InkListItem):
            return other.item_name == self.item_name and other.origin_name == self.origin_name
        return False

    def __hash__(self) -> int:
        origin_code = 0
        item_code = hash(self.item_name)
        if self.origin_name:
            origin_code = hash(self.origin_name)
        return origin_code + item_code

    @classproperty
    def Null(cls) -> "InkListItem":
        return InkListItem(None, None)

    @property
    def is_null(self) -> bool:
        return self.item_name is self.origin_name is None

    @property
    def full_name(self) -> str:
        return self.origin_name or "?" + "." + self.item_name


class InkList(UserDict):
    _origin_names: List[str]
    origins: List["ListDefinition"]
    data: Dict[InkListItem, int]

    def __init__(self, pri: Union["InkList", str, Tuple[InkListItem, int]] = None, sec: "Story" = None):
        self._origin_names = []
        self.origins = []
        self.data = {}
        if isinstance(pri, InkList):
            self.data = pri.data
            self._origin_names = pri.origin_names
        elif isinstance(pri, str):
            self.set_initial_origin_name(pri)
            list_def = sec.list_definitions.get(pri)
            if list_def:
                self.origins = [list_def]
            else:
                raise ValueError("InkList origin could not be found in story when constructing new list: " + str(pri))
        else:
            key, value = pri
            self[key] = value

    def __str__(self) -> str:
        ordered = self.data.items()
        ordered = sorted(ordered, key=lambda x, y: x)

        sb = ""
        for i, (key, value) in enumerate(ordered):
            if i > 0:
                sb += ", "
            sb += key.item_name
        return sb

    def __hash__(self) -> int:
        return sum(map(hash, self.data))

    def __eq__(self, other):
        if isinstance(other, InkList):
            if len(self) != len(other):
                return False
            for key, value in self.items():
                if key not in other:
                    return False
            return True

        return False

    @property
    def origin_of_max_item(self) -> Optional["ListDefinition"]:
        if not self.origins:
            return None
        max_origin_name = self.max_item[0].origin_name
        for origin in self.origins:
            if origin.name == max_origin_name:
                return origin
        return None

    @property
    def origin_names(self) -> List[str]:
        if len(self) > 0:
            if not self._origin_names:
                self._origin_names = []
            else:
                self._origin_names.clear()

            for key, value in self.items():
                self._origin_names.append(key.origin_name)
        return self._origin_names

    @property
    def max_item(self) -> Tuple[InkListItem, int]:
        return max(self.items(), key=lambda key, value: value)

    @property
    def min_item(self) -> Tuple[InkListItem, int]:
        return min(self.items(), key=lambda key, value: value)

    @property
    def inverse(self) -> "InkList":
        ink_list = InkList()
        if self.origins:
            for origin in self.origins:
                for key, value in origin.items():
                    if key not in self:
                        ink_list[key] = value
        return ink_list

    @property
    def all(self) -> "InkList":
        ink_list = InkList()
        if self.origins:
            for origin in self.origins:
                for key, value in origin.items():
                    ink_list[key] = value
        return ink_list

    def add_item(self, item: Union[InkListItem, str]):
        if isinstance(item, InkListItem):
            if not item.origin_name:
                self.add_item(item.item_name)
                return
            for origin in self.origins:
                if origin.name == item.origin_name:
                    int_val = origin.get(item)
                    if int_val:
                        self[item] = int_val
                        return
                    else:
                        raise ValueError(
                            f"Could not add the item {item} to this list because it doesn't exist in the original list definition in ink.")
        else:
            found_list_def = None
            for origin in self.origins:
                if origin.contains_item_with_name(item):
                    if found_list_def:
                        raise ValueError(
                            "fCould not add the item {item} to this list because it could come from either " + origin.name + " or " + found_list_def.name)
                    else:
                        found_list_def = origin

    def contains_item_named(self, item_name: str) -> bool:
        for key, value in self.items():
            if key.item_name == item_name:
                return True
        return False

    def set_initial_origin_name(self, initial_origin_name: str):
        self._origin_names = [initial_origin_name]

    def set_initial_origin_names(self, initial_origin_names: List[str]):
        self._origin_names = initial_origin_names

    def union(self, other: "InkList") -> "InkList":
        union = InkList(self)
        for key, value in other.items():
            union[key] = value
        return union

    def intersect(self, other: "InkList") -> "InkList":
        intersection = InkList()
        for key, value in self.items():
            if key in other:
                intersection[key] = value
        return intersection

    def without(self, list_to_remove: "InkList") -> "InkList":
        result = InkList(self)
        for key, value in list_to_remove.items():
            result.pop(key)
        return result

    def contains(self, other: "InkList") -> bool:
        for key, value in other.items():
            if key not in self:
                return False
        return True

    def greater_than(self, other: "InkList") -> bool:
        if len(other) == 0:
            return True
        if len(self) == 0:
            return False
        return self.min_item[1] > other.max_item[1]

    def greater_than_or_equals(self, other: "InkList") -> bool:
        if len(other) == 0:
            return True
        if len(self) == 0:
            return False
        return self.min_item[1] >= other.min_item[1] and self.max_item[1] >= other.max_item[1]

    def less_than(self, other: "InkList") -> bool:
        if len(other) == 0:
            return False
        if len(self) == 0:
            return True
        return self.max_item[1] < other.min_item[1]

    def less_than_or_equals(self, other: "InkList") -> bool:
        if len(other) == 0:
            return False
        if len(self) == 0:
            return True
        return self.max_item[1] <= other.max_item[1] and self.min_item[1] <= other.min_item[1]

    def max_as_list(self) -> "InkList":
        if len(self) > 0:
            return InkList(self.max_item)
        else:
            return InkList()

    def min_as_list(self) -> "InkList":
        if len(self) > 0:
            return InkList(self.min_item)
        else:
            return InkList()
