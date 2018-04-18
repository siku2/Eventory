from enum import IntEnum, auto
from typing import Any, Optional, TYPE_CHECKING, Tuple

from .ink_list import InkList
from .object import Object
from .path import Path
from .story_exception import StoryException

if TYPE_CHECKING:
    from .ink_list import InkListItem


class ValueType(IntEnum):
    Int = auto
    Float = auto
    List = auto
    String = auto

    DivertTarget = auto
    VariablePointer = auto


class Value(Object):
    value_type: ValueType
    is_truthy: bool
    value: Any

    def __init__(self, val: Any):
        super().__init__()
        self.value = val

    def __str__(self) -> str:
        return str(self.value)

    @property
    def value_object(self) -> Any:
        return self.value

    @classmethod
    def create(cls, val: Any) -> Optional["Value"]:
        if isinstance(val, bool):
            val = int(val)
        if isinstance(val, int):
            return IntValue(val)
        elif isinstance(val, float):
            return FloatValue(val)
        elif isinstance(val, str):
            return StringValue(val)
        elif isinstance(val, Path):
            return DivertTargetValue(val)
        elif isinstance(val, InkList):
            return ListValue(val)
        return None

    def cast(self, new_type: ValueType) -> "Value":
        raise NotImplementedError

    def copy(self) -> Any:
        return self.create(self.value_object)

    def bad_cast_exception(self, target_type: ValueType) -> StoryException:
        return StoryException(f"Can't cast {self.value_object} from {self.value_type} to {target_type}")


class IntValue(Value):
    value_type: ValueType = ValueType.Int
    value: int

    def __init__(self, val: int = 0):
        super().__init__(val)

    @property
    def is_truthy(self) -> bool:
        return self.value != 0

    def cast(self, new_type: ValueType) -> Value:
        if new_type == self.value_type:
            return self
        if new_type == ValueType.Float:
            return FloatValue(float(self.value))
        if new_type == ValueType.String:
            return StringValue(str(self.value))

        raise self.bad_cast_exception(new_type)


class FloatValue(Value):
    value_type: ValueType = ValueType.Float
    value: float

    def __init__(self, val: float = 0.):
        super().__init__(val)

    @property
    def is_truthy(self) -> bool:
        return self.value != 0.

    def cast(self, new_type: ValueType) -> Value:
        if new_type == self.value_type:
            return self
        if new_type == ValueType.Int:
            return IntValue(int(self.value))
        if new_type == ValueType.String:
            return StringValue(str(self.value))

        raise self.bad_cast_exception(new_type)


class StringValue(Value):
    value_type: ValueType = ValueType.String
    value: str
    is_newline: bool
    is_inline_whitespace: bool

    def __init__(self, val: str = ""):
        super().__init__(val)
        self.is_newline = self.value == "\n"
        self.is_inline_whitespace = True
        for c in self.value:
            if c != " " and c != "\t":
                self.is_inline_whitespace = False
                break

    @property
    def is_truthy(self) -> bool:
        return len(self.value) > 0

    @property
    def is_non_whitespace(self) -> bool:
        return not self.is_newline and not self.is_inline_whitespace

    def cast(self, new_type: ValueType) -> Optional[Value]:
        if new_type == self.value_type:
            return self
        if new_type == ValueType.Int:
            if self.value.isnumeric():
                return IntValue(int(self.value))
            else:
                return None
        if new_type == ValueType.Float:
            try:
                parsed_float = float(self.value)
            except ValueError:
                return None
            else:
                return FloatValue(parsed_float)

        raise self.bad_cast_exception(new_type)


class DivertTargetValue(Value):
    value_type: ValueType = ValueType.DivertTarget
    value: Path

    def __init__(self, val: Path = None):
        super().__init__(val)

    def __str__(self) -> str:
        return f"DivertTargetValue({self.target_path})"

    @property
    def target_path(self) -> Path:
        return self.value

    @target_path.setter
    def target_path(self, value: Path):
        self.value = value

    @property
    def is_truthy(self) -> bool:
        raise Exception("Shouldn't be checking the truthiness of a divert target")

    def cast(self, new_type: ValueType) -> Value:
        if new_type == self.value_type:
            return self

        raise self.bad_cast_exception(new_type)


class VariablePointerValue(Value):
    value_type: ValueType = ValueType.VariablePointer
    value: str
    context_index: int

    def __init__(self, variable_name: str = None, context_index: int = -1):
        super().__init__(variable_name)
        self.context_index = context_index if variable_name else 0

    def __str__(self) -> str:
        return f"VariablePointerValue({self.variable_name})"

    @property
    def variable_name(self) -> str:
        return self.value

    @variable_name.setter
    def variable_name(self, value: str):
        self.value = value

    @property
    def is_truthy(self) -> bool:
        raise Exception("Shouldn't be checking the truthiness of a divert target")

    def cast(self, new_type: ValueType) -> Value:
        if new_type == self.value_type:
            return self

        raise self.bad_cast_exception(new_type)

    def copy(self) -> Any:
        return VariablePointerValue(self.variable_name, self.context_index)


class ListValue(Value):
    value_type: ValueType = ValueType.List
    value: InkList

    def __init__(self, *args):
        if len(args) == 2:
            args: Tuple["InkListItem", int]
            super().__init__(InkList(args))
        elif len(args) == 1:
            super().__init__(InkList(args[0]))
        else:
            super().__init__(None)

    @property
    def is_truthy(self) -> bool:
        for key, value in self.value.items():
            if value != 0:
                return True
        return False

    def cast(self, new_type: ValueType) -> Value:
        if new_type == self.value_type:
            return self
        if new_type == ValueType.Int:
            key, value = self.value.max_item
            if key.is_null:
                return IntValue(0)
            else:
                return IntValue(value)
        if new_type == ValueType.Float:
            key, value = self.value.max_item
            if key.is_null:
                return FloatValue(0.)
            else:
                return FloatValue(float(value))
        if new_type == ValueType.String:
            key, value = self.value.max_item
            if key.is_null:
                return StringValue("")
            else:
                return StringValue(str(value))

        raise self.bad_cast_exception(new_type)

    @staticmethod
    def retain_list_origins_for_assignment(old_value: Object, new_value: Object):
        if isinstance(old_value, ListValue) and isinstance(new_value, ListValue) and len(new_value.value) == 0:
            new_value.value.set_initial_origin_names(old_value.value.origin_names)
