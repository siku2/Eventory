from typing import Dict, Optional

from .ink_list import InkList, InkListItem
from .value import ListValue


class ListDefinition:
    _name: str
    _items: Dict[InkListItem, int]
    _item_name_to_values: Dict[str, int]

    def __init__(self, name: str, items: Dict[str, int]):
        self._name = name
        self._item_name_to_values = items

    @property
    def name(self):
        return self._name

    @property
    def items(self) -> Dict[InkListItem, int]:
        if not self._items:
            self._items = {}
            for key, value in self._item_name_to_values.items():
                item = InkListItem(self.name, key)
                self._items[item] = value
        return self._items

    def value_for_item(self, item: InkListItem) -> int:
        int_val = self._item_name_to_values.get(item.item_name)
        return int_val or 0

    def contains_item(self, item: InkListItem) -> bool:
        if item.origin_name != self.name:
            return False
        return item.item_name in self._item_name_to_values

    def contains_item_with_name(self, item_name: str) -> bool:
        return item_name in self._item_name_to_values

    def try_get_item_with_value(self, value: int) -> InkListItem:
        for key, val in self._item_name_to_values.items():
            if val == value:
                return InkListItem(self.name, key)
        return InkListItem.Null

    def try_get_value_for_item(self, item: InkListItem) -> Optional[int]:
        return self._item_name_to_values.get(item.item_name)

    def list_range(self, minimum: int, maximum: int) -> ListValue:
        raw_list = InkList()
        for key, value in self._item_name_to_values.items():
            if minimum <= value <= maximum:
                item = InkListItem(self.name, key)
                raw_list[item] = value
        return ListValue(raw_list)
