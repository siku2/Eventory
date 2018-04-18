from typing import Optional

from .object import Object
from .path import Path
from .push_pop import PushPopType


class Divert(Object):
    _target_path: "Path"
    _target_content: Object
    variable_divert_name: str
    pushes_to_stack: bool
    stack_push_type: PushPopType
    is_external: bool
    external_args: int
    is_conditional: bool

    def __init__(self, stack_push_type: PushPopType = None):
        super().__init__()
        self._target_path = None
        self._target_content = None
        self.variable_divert_name = ""
        self.pushes_to_stack = True if stack_push_type else False
        self.stack_push_type = stack_push_type
        self.is_external = False
        self.external_args = 0
        self.is_conditional = False

    def __eq__(self, other):
        if isinstance(other, Divert):
            if self.has_variable_target == other.has_variable_target:
                if self.has_variable_target:
                    return self.variable_divert_name == other.variable_divert_name
                else:
                    return self.target_path == other.target_path
        return False

    def __hash__(self):
        if self.has_variable_target:
            return hash(self.variable_divert_name) + 12345
        else:
            return hash(self.target_path) + 54321

    def __str__(self):
        if self.has_variable_target:
            return f"Divert(variable: {self.variable_divert_name})"
        elif not self.target_path:
            return "Divert(null)"
        else:
            sb = ""
            target_str = str(self.target_path)
            target_line_num = self.debug_line_number_of_path(self.target_path)
            if target_line_num:
                target_str = f"line {target_line_num}"

            sb += "Divert"
            if self.is_conditional:
                sb += "?"
            if self.pushes_to_stack:
                if self.stack_push_type == PushPopType.Function:
                    sb += " function"
                else:
                    sb += " tunnel"
            sb += f" -> {self.target_path_string} ({target_str})"
            return sb

    @property
    def target_path(self) -> "Path":
        if self._target_path and self._target_path.is_relative:
            target_obj = self.target_content
            if target_obj:
                self._target_path = target_obj.path
        return self._target_path

    @target_path.setter
    def target_path(self, value: "Path"):
        self._target_path = value
        self._target_content = None

    @property
    def target_content(self) -> Object:
        if not self._target_content:
            self._target_content = self.resolve_path(self._target_path)
        return self._target_content

    @property
    def target_path_string(self) -> Optional[str]:
        if not self.target_path:
            return None
        return self.compact_path_string(self.target_path)

    @target_path_string.setter
    def target_path_string(self, value: str):
        if not value:
            self.target_path = None
        else:
            self.target_path = Path(value)

    @property
    def has_variable_target(self):
        return bool(self.variable_divert_name)
