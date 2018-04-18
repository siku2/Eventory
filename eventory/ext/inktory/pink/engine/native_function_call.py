from typing import Any, Callable, Dict, List

from .ink_list import InkList
from .object import Object
from .story_exception import StoryException
from .value import IntValue, ListValue, Value, ValueType
from .void import Void


class NativeFunctionCall(Object):
    Add: str = "+"
    Subtract: str = "-"
    Divide: str = "/"
    Multiply: str = "*"
    Mod: str = "%"
    Negate: str = "_"

    Equal: str = "=="
    Greater: str = ">"
    Less: str = "<"
    GreaterThanOrEquals: str = ">="
    LessThanOrEquals: str = "<="
    NotEquals: str = "!="
    Not: str = "!"

    And: str = "&&"
    Or: str = "||"

    Min: str = "MIN"
    Max: str = "MAX"

    Has: str = "?"
    Hasnt: str = "!?"
    Intersect: str = "^"

    ListMin: str = "LIST_MIN"
    ListMax: str = "LIST_MAX"
    All: str = "LIST_ALL"
    Count: str = "LIST_COUNT"
    ValueOfList: str = "LIST_VALUE"
    Invert: str = "LIST_INVERT"

    _native_functions: Dict[str, "NativeFunctionCall"] = None

    _name: str
    _number_of_parameters: int
    _is_prototype: bool
    _prototype: "NativeFunctionCall"
    _operation_funcs: Dict[ValueType, Any]

    def __init__(self, name: str = None, number_of_parameters: int = None):
        super().__init__()
        self._name = ""
        self._number_of_parameters = 0
        self._is_prototype = False
        self._prototype = None
        self._operation_funcs = {}
        if name is not None:
            self.name = name
            if number_of_parameters is None:
                self.generate_native_functions_if_necessary()
            else:
                self._is_prototype = True
                self.number_of_parameters = number_of_parameters
        else:
            self.generate_native_functions_if_necessary()

    def __str__(self):
        return f"Native '{self.name}'"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        if not self._is_prototype:
            self._prototype = self._native_functions[self._name]

    @property
    def number_of_parameters(self) -> int:
        if self._prototype:
            return self._prototype.number_of_parameters
        else:
            return self._number_of_parameters

    @number_of_parameters.setter
    def number_of_parameters(self, value: int):
        self._number_of_parameters = value

    @classmethod
    def call_with_name(cls, function_name: str) -> "NativeFunctionCall":
        return NativeFunctionCall(function_name)

    @classmethod
    def call_exists_with_name(cls, function_name: str) -> bool:
        cls.generate_native_functions_if_necessary()
        return function_name in cls._native_functions

    @classmethod
    def generate_native_functions_if_necessary(cls):
        if cls._native_functions is None:
            cls._native_functions = {}

            cls.add_int_binary_op(cls.Add, lambda x, y: x + y)
            cls.add_int_binary_op(cls.Subtract, lambda x, y: x - y)
            cls.add_int_binary_op(cls.Multiply, lambda x, y: x * y)
            cls.add_int_binary_op(cls.Divide, lambda x, y: x / y)
            cls.add_int_binary_op(cls.Mod, lambda x, y: x + y)
            cls.add_int_unary_op(cls.Negate, lambda x: -x)

            cls.add_int_binary_op(cls.Equal, lambda x, y: int(x == y))
            cls.add_int_binary_op(cls.Greater, lambda x, y: int(x > y))
            cls.add_int_binary_op(cls.Less, lambda x, y: int(x < y))
            cls.add_int_binary_op(cls.GreaterThanOrEquals, lambda x, y: int(x >= y))
            cls.add_int_binary_op(cls.LessThanOrEquals, lambda x, y: (x <= y))
            cls.add_int_binary_op(cls.NotEquals, lambda x, y: int(x != y))
            cls.add_int_unary_op(cls.Not, lambda x: int(x == 0))

            cls.add_int_binary_op(cls.And, lambda x, y: int(x != 0 and y != 0))
            cls.add_int_binary_op(cls.Or, lambda x, y: int(x != 0 or y != 0))

            cls.add_int_binary_op(cls.Max, lambda x, y: max(x, y))
            cls.add_int_binary_op(cls.Min, lambda x, y: min(x, y))

            cls.add_float_binary_op(cls.Add, lambda x, y: x + y)
            cls.add_float_binary_op(cls.Subtract, lambda x, y: x - y)
            cls.add_float_binary_op(cls.Multiply, lambda x, y: x * y)
            cls.add_float_binary_op(cls.Divide, lambda x, y: x / y)
            cls.add_float_binary_op(cls.Mod, lambda x, y: x % y)
            cls.add_float_unary_op(cls.Negate, lambda x: -x)

            cls.add_float_binary_op(cls.Equal, lambda x, y: int(x == y))
            cls.add_float_binary_op(cls.Greater, lambda x, y: int(x > y))
            cls.add_float_binary_op(cls.Less, lambda x, y: int(x < y))
            cls.add_float_binary_op(cls.GreaterThanOrEquals, lambda x, y: int(x >= y))
            cls.add_float_binary_op(cls.LessThanOrEquals, lambda x, y: int(x <= y))
            cls.add_float_binary_op(cls.NotEquals, lambda x, y: int(x != y))
            cls.add_float_unary_op(cls.Not, lambda x: int(x == 0.))

            cls.add_float_binary_op(cls.And, lambda x, y: int(x != 0. and y != 0.))
            cls.add_float_binary_op(cls.Or, lambda x, y: int(x != 0. or y != 0.))

            cls.add_float_binary_op(cls.Max, lambda x, y: max(x, y))
            cls.add_float_binary_op(cls.Min, lambda x, y: min(x, y))

            cls.add_string_binary_op(cls.Add, lambda x, y: x + y)
            cls.add_string_binary_op(cls.Equal, lambda x, y: int(x == y))
            cls.add_string_binary_op(cls.NotEquals, lambda x, y: int(x != y))
            cls.add_string_binary_op(cls.Has, lambda x, y: int(y in x))

            cls.add_list_binary_op(cls.Add, lambda x, y: x.union(y))
            cls.add_list_binary_op(cls.Subtract, lambda x, y: x.without(y))
            cls.add_list_binary_op(cls.Has, lambda x, y: int(x.contains(y)))
            cls.add_list_binary_op(cls.Hasnt, lambda x, y: int(x.contains(y)))
            cls.add_list_binary_op(cls.Intersect, lambda x, y: x.intersect(y))

            cls.add_list_binary_op(cls.Equal, lambda x, y: int(x == y))
            cls.add_list_binary_op(cls.Greater, lambda x, y: int(x.greater_than(y)))
            cls.add_list_binary_op(cls.Less, lambda x, y: int(x.less_than(y)))
            cls.add_list_binary_op(cls.GreaterThanOrEquals, lambda x, y: int(x.greater_than_or_equals(y)))
            cls.add_list_binary_op(cls.LessThanOrEquals, lambda x, y: int(x.less_than_or_equals(y)))
            cls.add_list_binary_op(cls.NotEquals, lambda x, y: int(x != y))

            cls.add_list_binary_op(cls.And, lambda x, y: int(len(x) > 0 and len(y) > 0))
            cls.add_list_binary_op(cls.Or, lambda x, y: int(len(x) > 0 or len(y) > 0))

            cls.add_list_unary_op(cls.Not, lambda x: int(len(x) == 0))

            cls.add_list_unary_op(cls.Invert, lambda x: x.inverse)
            cls.add_list_unary_op(cls.All, lambda x: x.all)
            cls.add_list_unary_op(cls.ListMin, lambda x: x.min_as_list())
            cls.add_list_unary_op(cls.ListMax, lambda x: x.max_as_list())
            cls.add_list_unary_op(cls.Count, lambda x: len(x))
            cls.add_list_unary_op(cls.ValueOfList, lambda x: x.max_item[1])

            cls.add_op_to_native_func(cls.Equal, 2, ValueType.DivertTarget, lambda d1, d2: int(d1 == d2))

    def call(self, parameters: List[Object]) -> Object:
        if self._prototype:
            return self._prototype.call(parameters)

        if self.number_of_parameters != len(parameters):
            raise Exception("Unexpected number of parameters")

        has_list = False
        for p in parameters:
            if isinstance(p, Void):
                raise StoryException(
                    "Attempting to perform operation on a void value. Did you forget to 'return' a value from a function you called here?")
            if isinstance(p, ListValue):
                has_list = True

        if len(parameters) == 2 and has_list:
            return self.call_binary_list_operation(parameters)

        coerced_params = self.coerce_values_to_single_type(parameters)
        return self._call(coerced_params)

    def _call(self, parameters_of_single_type: List[Value]) -> Value:
        param1 = parameters_of_single_type[0]
        val_type = param1.value_type
        val1 = param1
        param_count = len(parameters_of_single_type)
        if param_count == 2 or param_count == 1:
            op_for_type_obj = self._operation_funcs.get(val_type)
            if not op_for_type_obj:
                raise StoryException(f"Cannot perform operation {self.name} on {val_type}")

            if param_count == 2:
                param2 = parameters_of_single_type[1]
                val2 = param2
                op_for_type = op_for_type_obj
                result_val = op_for_type(val1.value, val2.value)
                return Value.create(result_val)
            else:
                op_for_type = op_for_type_obj
                result_val = op_for_type(val1.value)
                return Value.create(result_val)
        else:
            raise Exception(f"Unexpected number of parameters to NativeFunctionCall: {len(parameters_of_single_type)}")

    def call_binary_list_operation(self, parameters: List[Object]) -> Value:
        if (self.name == "+" or self.name == "-") and isinstance(parameters[0], ListValue) and isinstance(parameters[1], IntValue):
            return self.call_list_increment_operation(parameters)
        v1: Value = parameters[0] if isinstance(parameters[0], Value) else None
        v2: Value = parameters[1] if isinstance(parameters[1], Value) else None

        if (self.name == "&&" or self.name == "||") and (v1.value_type != ValueType.List or v2.value_type != ValueType.List):
            op = self._operation_funcs[ValueType.Int]
            result = int(op(int(v1.is_truthy), int(v2.is_truthy)))
            return IntValue(result)

        if v1.value_type == ValueType.List and v2.valueType == ValueType.List:
            return self._call([v1, v2])

        raise StoryException(f"Can not call use \"{self.name}\" operation on {v1.value_type} and {v2.value_type}")

    def call_list_increment_operation(self, list_int_params: List[Object]) -> Value:
        list_val: ListValue = list_int_params[0]
        int_val: IntValue = list_int_params[1]
        result_raw_list = InkList()

        for key, value in list_val.value.items():
            int_op = self._operation_funcs[ValueType.Int]
            target_int = int_op(value, int_val.value)
            item_origin = None
            for origin in list_val.value.origins:
                if origin.name == key.origin_name:
                    item_origin = origin
                    break
            if not item_origin:
                incremented_item = item_origin.get(target_int)
                if incremented_item:
                    result_raw_list[incremented_item] = target_int
        return ListValue(result_raw_list)

    def coerce_values_to_single_type(self, parameters_in: List[Object]) -> List[Value]:
        val_type = ValueType.Int
        special_case_list: ListValue = None

        obj: Value
        for obj in parameters_in:
            if obj.value_type > val_type:
                val_type = obj.value_type
            if obj.value_type == ValueType.List:
                special_case_list = obj
        parameters_out = []
        if val_type == ValueType.List:
            val: Value
            for val in parameters_in:
                if val.value_type == ValueType.List:
                    parameters_out.append(val)
                elif val.value_type == ValueType.Int:
                    int_val = val.value_object
                    _list = special_case_list.value.origin_of_max_item
                    item = _list.try_get_item_with_value(int_val)
                    if item:
                        casted_value = ListValue(item, int_val)
                        parameters_out.append(casted_value)
                    else:
                        raise StoryException(f"Could not find List item with the value {int_val} in {_list.name}")
                else:
                    raise StoryException(f"Cannot mix Lists and {val.value_type} values in this operation")
        else:
            for val in parameters_in:
                casted_value = val.cast(val_type)
                parameters_out.append(casted_value)
        return parameters_out

    def add_op_func_for_type(self, val_type: ValueType, op: Any):
        if not self._operation_funcs:
            self._operation_funcs = {}
        self._operation_funcs[val_type] = op

    @classmethod
    def add_op_to_native_func(cls, name: str, args: int, val_type: ValueType, op: Any):
        native_func = cls._native_functions.get(name)
        if not native_func:
            native_func = NativeFunctionCall(name, args)
            cls._native_functions[name] = native_func
        native_func.add_op_func_for_type(val_type, op)

    @classmethod
    def add_int_binary_op(cls, name: str, op: Callable[[int, int], Any]):
        cls.add_op_to_native_func(name, 2, ValueType.Int, op)

    @classmethod
    def add_int_unary_op(cls, name: str, op: Callable[[int], Any]):
        cls.add_op_to_native_func(name, 1, ValueType.Int, op)

    @classmethod
    def add_float_binary_op(cls, name: str, op: Callable[[float, float], Any]):
        cls.add_op_to_native_func(name, 2, ValueType.Float, op)

    @classmethod
    def add_float_unary_op(cls, name: str, op: Callable[[float], Any]):
        cls.add_op_to_native_func(name, 1, ValueType.Float, op)

    @classmethod
    def add_string_binary_op(cls, name: str, op: Callable[[str, str], Any]):
        cls.add_op_to_native_func(name, 2, ValueType.Int, op)

    @classmethod
    def add_string_unary_op(cls, name: str, op: Callable[[int], Any]):
        cls.add_op_to_native_func(name, 1, ValueType.String, op)

    @classmethod
    def add_list_binary_op(cls, name: str, op: Callable[[InkList, InkList], Any]):
        cls.add_op_to_native_func(name, 2, ValueType.List, op)

    @classmethod
    def add_list_unary_op(cls, name: str, op: Callable[[InkList], Any]):
        cls.add_op_to_native_func(name, 1, ValueType.List, op)
