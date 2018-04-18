from typing import TYPE_CHECKING

from .object import Object

if TYPE_CHECKING:
    from .path import Path
    from .container import Container


class ChoicePoint(Object):
    _path_on_choice: "Path"

    def __init__(self, once_only=True):
        super().__init__()
        self._path_on_choice = None
        self.has_condition = False
        self.has_start_content = False
        self.has_choice_only_content = False
        self.once_only = once_only
        self.is_invisible_default = False

    def __str__(self):
        target_line_num = self.debug_line_number_of_path(self.path_on_choice)
        target_string = str(self.path_on_choice)

        if target_line_num:
            target_string = " line " + str(target_line_num)
        return "Choice: -> " + target_string

    @property
    def path_on_choice(self) -> "Path":
        if self._path_on_choice and self._path_on_choice.is_relative:
            choice_target_obj = self.choice_target
            if choice_target_obj:
                self._path_on_choice = choice_target_obj.path
        return self._path_on_choice

    @path_on_choice.setter
    def path_on_choice(self, value: "Path"):
        self._path_on_choice = value

    @property
    def choice_target(self) -> "Container":
        return self.resolve_path(self._path_on_choice)

    @property
    def path_string_on_choice(self) -> str:
        return self.compact_path_string(self.path_on_choice)

    @path_string_on_choice.setter
    def path_string_on_choice(self, value: str):
        self.path_on_choice = Path(value)

    @property
    def flags(self) -> int:
        flags = 0
        if self.has_condition:
            flags |= 1
        if self.has_start_content:
            flags |= 2
        if self.has_choice_only_content:
            flags |= 4
        if self.is_invisible_default:
            flags |= 8
        if self.once_only:
            flags |= 16
        return flags

    @flags.setter
    def flags(self, value: int):
        self.has_condition = (value & 1) > 0
        self.has_start_content = (value & 2) > 0
        self.has_choice_only_content = (value & 4) > 0
        self.is_invisible_default = (value & 8) > 0
        self.once_only = (value & 16) > 0
