from typing import List, TYPE_CHECKING

from .object import Object
from .json_serialisation import Json
import json
from .container import Container
from .pointer import Pointer

if TYPE_CHECKING:
    from .choice import Choice
    from .variables_state import VariablesState
    from .list_definition_origin import ListDefinitionOrigin
    from .story_state import StoryState
    from .path import Path
    from .search_result import SearchResult


class Story(Object):
    ink_version_current: int = 18
    ink_version_minimum_compatible: int = 18

    def __init__(self):
        pass

    @property
    def current_choices(self) -> List["Choice"]:
        choices = []
        for c in self._state.current_choices:
            if not c.is_invisible_default:
                c.index = len(choices)
                choices.append(c)
        return choices

    @property
    def current_text(self) -> str:
        return self.state.current_text

    @property
    def current_tags(self) -> List[str]:
        return self.state.current_tags

    @property
    def current_errors(self) -> List[str]:
        return self.state.current_errors

    @property
    def current_warnings(self) -> List[str]:
        return self.state.current_warnings

    @property
    def has_error(self) -> bool:
        return self.state.has_error

    @property
    def has_warning(self) -> bool:
        return self.state.has_warning

    @property
    def variables_state(self) -> "VariablesState":
        return self.state.variables_state

    @property
    def list_definitions(self) -> "ListDefinitionOrigin":
        return self._list_definitions

    @property
    def state(self) -> "StoryState":
        return self._state

    def start_profiling(self) -> Profiler:
        self._profiler = Profiler()
        return self._profiler

    def end_profiling(self):
        self._profiler = None

    def to_json_string(self) -> str:
        root_container_json_list = Json.runtime_object_to_j_token(self._main_content_container)
        root_object = {}
        root_object["inkVersion"] = self.ink_version_current
        root_object["root"] = root_container_json_list
        if self._list_definitions:
            root_object["listDefs"] = Json.list_definitions_to_j_token(self._list_definitions)
        return json.dumps(root_object)

    def reset_state(self):
        self._state = StoryState(self)
        self._state.variables_state.variable_changed_event # TODO
        self.reset_globals()

    def reset_errors(self):
        self._state.reset_errors()

    def reset_callstack(self):
        self._state.force_end()

    def reset_globals(self):
        if "global decl" in self._main_content_container.named_content:
            original_pointer = self.state.current_pointer
            self.choose_path_string("global decl", reset_callstack=False)
            self.continue_internal()
            self.state.current_pointer = original_pointer
        self.state.variables_state.snapshot_default_globals()

    def can_continue(self) -> bool:
        return self.state.can_continue

    def content_at_path(self, path: "Path") -> "SearchResult":
        return self.main_content_container.content_at_path(path)

    def knot_container_with_name(self, name:str) -> Optional[Container]:
        named_container = self.main_content_container.named_content.get(name)
        return named_container if isinstance(named_container, Container) else None

    def pointer_at_path(self, path: "Path") -> "Pointer":
        if path.length == 0:
            return Pointer.Null