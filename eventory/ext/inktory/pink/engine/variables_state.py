from typing import Any, Callable, Dict, Set

from .call_stack import CallStack
from .json_serialisation import Json
from .list_definition_origin import ListDefinitionOrigin
from .object import Object
from .story_exception import StoryException
from .value import ListValue, Value, VariablePointerValue
from .variable_assignment import VariableAssignment


class Event:
    _listeners: Set(Callable)

    def __init__(self):
        self._listeners = set()

    def __call__(self, *args, **kwargs):
        self.emit(*args, **kwargs)

    def emit(self, *args, **kwargs):
        for listener in self._listeners:
            listener(*args, **kwargs)

    def listen(self, listener: Callable):
        self._listeners.add(listener)


class VariablesState:
    _batch_observing_variable_changes: bool
    _global_variables: Dict[str, Object]
    _default_global_variables: Dict[str, Object]
    _changed_variables: Set[str]
    _list_defs_origin: ListDefinitionOrigin
    call_stack: CallStack
    variable_changed_event: Event

    def __init__(self, call_stack: CallStack, list_defs_origin: ListDefinitionOrigin):
        self._global_variables = {}
        self._list_defs_origin = list_defs_origin
        self.call_stack = call_stack
        self.variable_changed_event = Event()

    def __iter__(self):
        return iter(self._global_variables.keys())

    def __getitem__(self, item: str):
        value = self._global_variables.get(item)
        value = self._default_global_variables.get(value, value)
        return value

    def __setitem__(self, key, value):
        if key not in self._default_global_variables:
            raise StoryException("Cannot assign to a variable that hasn't been declared in the story")

        val = Value.create(value)
        if val is None:
            if value is None:
                raise StoryException("Cannot pass None to VariableState")
            else:
                raise StoryException(f"Invalid valud passed to VariableState: {str(value)}")

        self.set_global(key, val)

    @property
    def batch_observing_variable_changes(self) -> bool:
        return self._batch_observing_variable_changes

    @batch_observing_variable_changes.setter
    def batch_observing_variable_changes(self, value: bool):
        self._batch_observing_variable_changes = value
        if value:
            self._changed_variables = set()
        else:
            if self._changed_variables:
                for variable_name in self._changed_variables:
                    current_value = self._global_variables[variable_name]
                    self.variable_changed_event(variable_name, current_value)
            self._changed_variables = None

    @property
    def json_token(self) -> Dict[str, Any]:
        return Json.dictionary_runtime_objs_to_j_object(self._global_variables)

    @json_token.setter
    def json_token(self, value: Dict[str, Any]):
        self._global_variables = Json.j_object_to_dictionary_runtime_objs(value)

    def copy_from(self, to_copy: "VariablesState"):
        self._global_variables = to_copy._global_variables.copy()
        self._default_global_variables = to_copy._default_global_variables.copy()
        self.variable_changed_event = to_copy.variable_changed_event

        if to_copy.batch_observing_variable_changes != self.batch_observing_variable_changes:
            if to_copy.batch_observing_variable_changes:
                self._batch_observing_variable_changes = True
                self._changed_variables = to_copy._changed_variables.copy()
            else:
                self._batch_observing_variable_changes = False
                self._changed_variables = None

    def try_get_default_variable_value(self, name: str) -> Object:
        return self._default_global_variables.get(name)

    def global_variable_exists_with_name(self, name: str) -> bool:
        return name in self._global_variables

    def get_variable_with_name(self, name: str, context_index: int = -1) -> Object:
        var_value = self.get_raw_variable_with_name(name, context_index)

        if isinstance(var_value, VariablePointerValue):
            var_value = self.value_at_variable_pointer(var_value)
        return var_value

    def get_raw_variable_with_name(self, name: str, context_index: int) -> Object:
        if context_index == 0 or context_index == -1:
            var_value = self._global_variables.get(name)
            if var_value:
                return var_value
            list_item_value = self._list_defs_origin.find_single_item_list_with_name(name)
            if list_item_value:
                return list_item_value
        var_value = self.call_stack.get_temporary_variable_with_name(name, context_index)
        return var_value

    def value_at_variable_pointer(self, pointer: VariablePointerValue) -> Object:
        return self.get_variable_with_name(pointer.variable_name, pointer.context_index)

    def assign(self, var_ass: VariableAssignment, value: Object):
        name = var_ass.variable_name
        context_index = -1
        set_global = False
        if var_ass.is_new_declaration:
            set_global = var_ass.is_global
        else:
            set_global = name in self._global_variables
        if var_ass.is_new_declaration:
            if isinstance(value, VariablePointerValue):
                fully_resolved_variable_pointer = self.resolve_variable_pointer(value)
                value = fully_resolved_variable_pointer
        else:
            while True:
                existing_pointer = self.get_raw_variable_with_name(name, context_index)
                if isinstance(existing_pointer, VariablePointerValue):
                    name = existing_pointer.variable_name
                    context_index = existing_pointer.context_index
                    set_global = context_index == 0
                else:
                    break
        if set_global:
            self.set_global(name, value)
        else:
            self.call_stack.set_temporary_variable(name, value, var_ass.is_new_declaration, context_index)

    def snapshot_default_globals(self):
        self._default_global_variables = self._global_variables.copy()

    def retain_list_origins_for_assignment(self, old_value: Object, new_value: Object):
        if isinstance(old_value, ListValue) and isinstance(new_value, ListValue) and len(new_value.value) == 0:
            new_value.value.set_initial_origin_names(old_value.value.origin_names)

    def set_global(self, variable_name: str, value: Object):
        old_value = self._global_variables.get(variable_name)
        ListValue.retain_list_origins_for_assignment(old_value, value)
        self._global_variables[variable_name] = value
        if self.variable_changed_event and value is not old_value:
            if self.batch_observing_variable_changes:
                self._changed_variables.add(variable_name)
            else:
                self.variable_changed_event(variable_name, value)

    def resolve_variable_pointer(self, var_pointer: VariablePointerValue) -> VariablePointerValue:
        context_index = var_pointer.context_index
        if context_index == -1:
            context_index = self.get_context_index_of_variable_named(var_pointer.variable_name)
        value_of_variable_pointed_to = self.get_raw_variable_with_name(var_pointer.variable_name, context_index)
        if isinstance(value_of_variable_pointed_to, VariablePointerValue):
            return value_of_variable_pointed_to
        else:
            return VariablePointerValue(var_pointer.variable_name, context_index)

    def get_context_index_of_variable_named(self, var_name: str) -> int:
        if var_name in self._global_variables:
            return 0
        return self.call_stack.current_element_index
