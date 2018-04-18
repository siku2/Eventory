from typing import Dict, List, Optional, TYPE_CHECKING

from .value import ListValue

if TYPE_CHECKING:
    from .list_definition import ListDefinition


class ListDefinitionOrigin:
    _lists: Dict[str, "ListDefinition"]
    _all_unambiguous_list_value_cache: Dict[str, ListValue]

    def __init__(self, lists: List["ListDefinition"]):
        self._lists = {}
        self._all_unambiguous_list_value_cache = {}
        for _list in lists:
            self._lists[_list.name] = _list
            for key, value in _list.items.items():
                list_value = ListValue(key, value)
                self._all_unambiguous_list_value_cache[key.item_name] = list_value
                self._all_unambiguous_list_value_cache[key.full_name] = list_value

    @property
    def lists(self) -> List["ListDefinition"]:
        list_of_lists = []
        for key, value in self._lists.items():
            list_of_lists.append(value)
        return list_of_lists

    def try_list_get_definition(self, name: str) -> Optional["ListDefinition"]:
        return self._lists.get(name)

    def find_single_item_list_with_name(self, name: str) -> Optional[ListValue]:
        return self._all_unambiguous_list_value_cache.get(name)
