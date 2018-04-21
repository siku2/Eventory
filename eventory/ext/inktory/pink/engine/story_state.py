import json
import random
from typing import Any, Dict, List, Optional, Union

from .call_stack import CallStack, Thread
from .choice import Choice
from .container import Container
from .control_command import CommandType, ControlCommand
from .glue import Glue
from .json_serialisation import Json
from .object import Object
from .path import Path
from .pointer import Pointer
from .push_pop import PushPopType
from .story_exception import StoryException
from .tag import Tag
from .utils import late_import_from, remove_range_from_list
from .value import ListValue, StringValue, Value, ValueType
from .variables_state import VariablesState
from .void import Void

Story = late_import_from(".story", "Story")


class StoryState:
    k_ink_save_state_version: int = 8
    k_min_compatible_load_version: int = 8

    _current_text: str
    _current_tags: List[str]
    _output_stream: List[Object]
    _output_stream_text_dirty: bool = True
    _output_stream_tags_dirty: bool = True
    _current_choices: List[Choice]
    current_errors: List[str]
    current_warnings: List[str]
    variables_state: VariablesState
    call_stack: CallStack
    evaluation_stack: List[Object]
    diverted_pointer: Pointer
    visit_counts: Dict[str, int]
    turn_indices: Dict[str, int]
    current_turn_index: int
    story_seed: int
    previous_random: int
    did_safe_exit: bool
    story: Story

    def __init__(self, story: Story):
        self._current_text = None
        self._current_tags = []
        self._output_stream = []
        self.current_errors = []
        self.current_warnings = []
        self.diverted_pointer = None
        self.did_safe_exit = False

        self.story = story
        self._output_stream = []
        self.output_stream_dirty()

        self.evaluation_stack = []

        self.call_stack = CallStack(story.root_content_container)
        self.variables_state = VariablesState(self.call_stack, story.list_definitions)

        self.visit_counts = {}
        self.turn_indices = {}
        self.current_turn_index = -1

        self.story_seed = random.randrange(100)
        self.previous_random = 0

        self._current_choices = []
        self.go_to_start()

    @property
    def callstack_depth(self) -> int:
        return self.call_stack.depth

    @property
    def output_stream(self) -> List[Object]:
        return self._output_stream

    @property
    def current_choices(self) -> List[Choice]:
        if self.can_continue:
            return []
        return self._current_choices

    @property
    def generated_choices(self) -> List[Choice]:
        return self._current_choices

    @property
    def current_path_string(self) -> Optional[str]:
        pointer = self.current_pointer
        if pointer.is_null:
            return None
        else:
            return str(pointer.path)

    @property
    def current_pointer(self) -> Pointer:
        return self.call_stack.current_element.current_pointer

    @current_pointer.setter
    def current_pointer(self, value: Pointer):
        self.call_stack.current_element.current_pointer = value

    @property
    def previous_pointer(self) -> Pointer:
        return self.call_stack.current_thread.previous_pointer

    @previous_pointer.setter
    def previous_pointer(self, value: Pointer):
        self.call_stack.current_thread.previous_pointer = value

    @property
    def can_continue(self) -> bool:
        return not self.current_pointer.is_null and not self.has_error

    @property
    def has_error(self) -> bool:
        return self.current_errors and len(self.current_errors) > 0

    @property
    def has_warning(self) -> bool:
        return self.current_warnings and len(self.current_warnings) > 0

    @property
    def current_text(self) -> str:
        if self._output_stream_text_dirty:
            sb = ""
            for output_obj in self._output_stream:
                if isinstance(output_obj, StringValue):
                    sb += output_obj.value
            self._current_text = sb
            self._output_stream_dirty = False
        return self._current_text

    @property
    def current_tags(self) -> List[str]:
        if self._output_stream_tags_dirty:
            self._current_tags = []
            for output_obj in self._output_stream:
                if isinstance(output_obj, Tag):
                    self._current_tags.append(output_obj.text)
            self._output_stream_tags_dirty = False
        return self._current_tags

    @property
    def in_expression_evaluation(self) -> bool:
        return self.call_stack.current_element.in_expression_evaluation

    @in_expression_evaluation.setter
    def in_expression_evaluation(self, value: bool):
        self.call_stack.current_element.in_expression_evaluation = value

    @property
    def output_stream_ends_in_newline(self):
        if len(self._output_stream) > 0:
            for obj in reversed(self._output_stream):
                if isinstance(obj, ControlCommand):
                    break
                if isinstance(obj, StringValue):
                    if obj.is_newline:
                        return True
                    elif obj.is_non_whitespace:
                        break
        return False

    @property
    def output_stream_contains_content(self) -> bool:
        for content in self._output_stream:
            if isinstance(content, StringValue):
                return True
        return False

    @property
    def in_string_evaluation(self) -> bool:
        for cmd in reversed(self._output_stream):
            if isinstance(cmd, ControlCommand) and cmd.command_type == CommandType.BeginString:
                return True
        return False

    @property
    def json_token(self) -> Dict[str, Any]:
        obj = {}
        choice_threads = None
        for c in self._current_choices:
            c.original_thread_index = c.thread_at_generation.thread_index
            if self.call_stack.thread_with_index(c.original_thread_index) is None:
                if choice_threads is None:
                    choice_threads = {}
                choice_threads[str(c.original_thread_index)] = c.thread_at_generation.json_token
        if choice_threads:
            obj["choiceThreads"] = choice_threads

        obj["callstackThreads"] = self.call_stack.get_json_token()
        obj["variablesState"] = self.variables_state.json_token
        obj["evalStack"] = Json.list_to_jarray(self.evaluation_stack)
        obj["outputStream"] = Json.list_to_jarray(self._output_stream)
        obj["currentChoices"] = Json.list_to_jarray(self._current_choices)

        if not self.diverted_pointer.is_null:
            obj["currentDivertTarget"] = self.diverted_pointer.path.components_string

        obj["visitCounts"] = Json.int_dictionary_to_j_object(self.visit_counts)
        obj["turnIndices"] = Json.int_dictionary_to_j_object(self.turn_indices)
        obj["turnIdx"] = self.current_turn_index
        obj["storySeed"] = self.story_seed
        obj["previousRandom"] = self.previous_random

        obj["inkSaveVersion"] = self.k_ink_save_state_version
        obj["inkFormatVersion"] = self.story.ink_version_current

        return obj

    @json_token.setter
    def json_token(self, value: Dict[str, Any]):
        j_object = value
        j_save_version = j_object.get("inkSaveVersion")
        if j_save_version is None:
            raise StoryException("ink save format incorrect, can't load.")
        elif int(j_save_version) < self.k_min_compatible_load_version:
            raise StoryException(
                f"Ink save format isn't compatible with the current version (saw '{j_save_version}', but minimum is {self.k_min_compatible_load_version}), so can't load.")

        self.call_stack.set_json_token(j_object["callstackThreads"], self.story)
        self.variables_state.json_token = j_object["variablesState"]
        self.evaluation_stack = Json.j_array_to_runtime_obj_list(j_object["evalStack"])
        self._output_stream = Json.j_array_to_runtime_obj_list(j_object["outputStream"])
        self.output_stream_dirty()
        self._current_choices = Json.j_array_to_runtime_obj_list(j_object["currentChoices"])
        current_divert_target_path = j_object.get("currentDivertTarget")
        if current_divert_target_path:
            divert_path = Path(current_divert_target_path)
            self.diverted_pointer = self.story.pointer_at_path(divert_path)
        self.visit_counts = Json.j_object_to_int_dictionary(j_object["visitCounts"])
        self.turn_indices = Json.j_object_to_int_dictionary(j_object["turnIndices"])
        self.current_turn_index = int(j_object["turnIdx"])
        self.story_seed = int(j_object["storySeed"])
        self.previous_random = int(j_object["previousRandom"])
        j_choice_threads_obj = j_object.get("choiceThreads", {})
        for c in self._current_choices:
            found_active_thread = self.call_stack.thread_with_index(c.original_thread_index)
            if found_active_thread:
                c.thread_at_generation = found_active_thread
            else:
                j_saved_choice_thread = j_choice_threads_obj[str(c.original_thread_index)]
                c.thread_at_generation = Thread(j_saved_choice_thread, self.story)

    def to_json(self) -> str:
        return json.dumps(self.json_token)

    def load_json(self, _json: str):
        self.json_token = json.loads(_json)

    def visit_count_at_path_string(self, path_string: str) -> int:
        visit_count_out = self.visit_counts.get(path_string)
        return visit_count_out or 0

    def go_to_start(self):
        self.call_stack.current_element.current_pointer = Pointer.start_of(self.story.main_content_container)

    def copy(self) -> "StoryState":
        copy = StoryState(self.story)
        copy.output_stream.extend(self._output_stream)
        self.output_stream_dirty()
        copy._current_choices.extend(self._current_choices)
        if self.has_error:
            copy.current_errors = []
            copy.current_errors.extend(self.current_errors)
        if self.has_warning:
            copy.current_warnings = []
            copy.current_warnings.extend(self.current_warnings)
        copy.call_stack = CallStack(self.call_stack)
        copy.variables_state = VariablesState(copy.call_stack, self.story.list_definitions)
        copy.variables_state.copy_from(self.variables_state)
        copy.evaluation_stack.extend(self.evaluation_stack)
        if not self.diverted_pointer.is_null:
            copy.diverted_pointer = self.diverted_pointer
        copy.previous_pointer = self.previous_pointer
        copy.visit_counts = self.visit_counts.copy()
        copy.turn_indices = self.turn_indices.copy()
        copy.current_turn_index = self.current_turn_index
        copy.story_seed = self.story_seed
        copy.previous_random = self.previous_random
        copy.did_safe_exit = self.did_safe_exit
        return copy

    def reset_errors(self):
        self.current_errors = None
        self.current_warnings = None

    def reset_output(self, objs: List[Object] = None):
        self._output_stream.clear()
        if objs:
            self._output_stream.extend(objs)
            self.output_stream_dirty()

    def push_to_output_stream(self, obj: Object):
        if isinstance(obj, StringValue):
            list_text = self.try_splitting_head_tail_whitespace(obj)
            if list_text:
                for text_obj in list_text:
                    self.push_to_output_stream_individual(text_obj)
                self.output_stream_dirty()
                return
        self.push_to_output_stream_individual(obj)
        self.output_stream_dirty()

    def pop_from_output_stream(self, count: int):
        remove_range_from_list(self.output_stream, -count, len(self.output_stream))
        self.output_stream_dirty()

    def try_splitting_head_tail_whitespace(self, single: StringValue) -> Optional[List[StringValue]]:
        string = single.value
        head_last_newline_idx = -1
        head_first_newline_idx = -1
        for i in range(len(string)):
            c = string[i]
            if c == "\n":
                if head_first_newline_idx == -1:
                    head_first_newline_idx = i
                head_last_newline_idx = i
            elif c == " " or c == "\t":
                continue
            else:
                break
        tail_last_newline_idx = -1
        tail_first_newline_idx = -1
        for i in range(len(string)):
            c = string[i]
            if c == "\n":
                if tail_last_newline_idx == -1:
                    tail_last_newline_idx = i
                tail_first_newline_idx = i
            elif c == " " or c == "\t":
                continue
            else:
                break
        if head_first_newline_idx == -1 and tail_last_newline_idx == -1:
            return None

        list_texts = []
        inner_str_start = 0
        inner_str_end = len(string)
        if head_first_newline_idx != -1:
            if head_first_newline_idx > 0:
                leading_spaces = StringValue(string[:head_first_newline_idx])
                list_texts.append(leading_spaces)
            list_texts.append(StringValue("\n"))
            inner_str_start = head_last_newline_idx + 1
        if tail_last_newline_idx != -1:
            inner_str_end = tail_first_newline_idx
        if inner_str_end > inner_str_start:
            list_texts.append(StringValue(string[inner_str_start:inner_str_end]))
        if tail_last_newline_idx != -1 and tail_first_newline_idx > head_last_newline_idx:
            list_texts.append(StringValue("\n"))
            if tail_last_newline_idx < len(string) - 1:
                trailing_spaces = StringValue(string[tail_last_newline_idx + 1:])
                list_texts.append(trailing_spaces)
        return list_texts

    def push_to_output_stream_individual(self, obj: Object):
        include_in_output = True
        if isinstance(obj, Glue):
            self.trim_newlines_from_output_stream()
            include_in_output = True
        elif isinstance(obj, StringValue):
            function_trim_index = -1
            curr_el = self.call_stack.current_element
            if curr_el.element_type == PushPopType.Function:
                function_trim_index = curr_el.function_start_in_output_stream
            glue_trim_index = -1
            for i, o in enumerate(reversed(self._output_stream)):
                if isinstance(o, Glue):
                    glue_trim_index = i
                    break
                elif isinstance(o, ControlCommand) and o.command_type == CommandType.BeginString:
                    if i >= function_trim_index:
                        function_trim_index = -1
                    break
            if glue_trim_index != -1 and function_trim_index != -1:
                trim_index = min(function_trim_index, glue_trim_index)
            elif glue_trim_index != -1:
                trim_index = glue_trim_index
            else:
                trim_index = function_trim_index
            if trim_index != -1:
                if obj.is_newline:
                    include_in_output = False
                elif obj.is_non_whitespace:
                    if glue_trim_index > -1:
                        self.remove_existing_glue()
                    if function_trim_index > -1:
                        callstack_elements = self.call_stack.elements
                        for el in reversed(callstack_elements):
                            if el.element_type == PushPopType.Function:
                                el.function_start_in_output_stream = -1
                            else:
                                break
            elif obj.is_newline:
                if self.output_stream_ends_in_newline or not self.output_stream_contains_content:
                    include_in_output = False
        if include_in_output:
            self._output_stream.append(obj)
            self.output_stream_dirty()

    def trim_newlines_from_output_stream(self):
        remove_whitespace_from = -1
        i = len(self._output_stream) - 1
        while i >= 0:
            obj = self._output_stream[i]
            if isinstance(obj, ControlCommand) or (isinstance(obj, StringValue) and obj.is_non_whitespace):
                break
            elif isinstance(obj, StringValue) and obj.is_newline:
                remove_whitespace_from = i
            i -= 1

        if remove_whitespace_from >= 0:
            i = remove_whitespace_from
            while i < len(self._output_stream):
                text = self._output_stream[i]
                if isinstance(text, StringValue):
                    self._output_stream.pop(i)
                else:
                    i += 1
        self.output_stream_dirty()

    def remove_existing_glue(self):
        for obj in reversed(self._output_stream):
            if isinstance(obj, Glue):
                self._output_stream.remove(obj)
            elif isinstance(obj, ControlCommand):
                break
        self.output_stream_dirty()

    def push_evaluation_stack(self, obj: Object):
        if isinstance(obj, ListValue):
            raw_list = obj.value
            if raw_list.origin_names:
                if not raw_list.origins:
                    raw_list.origins = []
                raw_list.origins.clear()
                for n in raw_list.origin_names:
                    definition = self.story.list_definitions.try_list_get_definition(n)
                    if definition not in raw_list.origins:
                        raw_list.origins.append(definition)
        self.evaluation_stack.append(obj)

    def peek_evaluation_stack(self) -> Object:
        return self.evaluation_stack[-1]

    def _pop_evaluation_stack(self) -> Object:
        obj = self.evaluation_stack.pop(-1)
        return obj

    def pop_evaluation_stack(self, number_of_objects: int = None) -> Union[List[Object], Object]:
        if number_of_objects is None:
            return self._pop_evaluation_stack()

        if number_of_objects > len(self.evaluation_stack):
            raise Exception("Trying to pop too many objects")

        popped = self.evaluation_stack[-number_of_objects:]
        remove_range_from_list(self.evaluation_stack, -number_of_objects, len(self.evaluation_stack))
        return popped

    def force_end(self):
        while self.call_stack.can_pop_thread:
            self.call_stack.pop_thread()
        while self.call_stack.can_pop:
            self.pop_callstack()
            self._current_choices.clear()
            self.current_pointer = Pointer.Null
            self.previous_pointer = Pointer.Null
            self.did_safe_exit = True

    def trim_whitespace_from_function_end(self):
        assert self.call_stack.current_element.element_type == PushPopType.Function
        function_start_point = self.call_stack.current_element.function_start_in_output_stream

        if function_start_point == -1:
            function_start_point = 0

        for i in range(len(self.output_stream) - 1, function_start_point, -1):
            obj = self._output_stream[i]
            if not isinstance(obj, StringValue):
                continue
            if isinstance(obj, ControlCommand):
                break
            if obj.is_newline or obj.is_inline_whitespace:
                self._output_stream.pop(i)
                self.output_stream_dirty()
            else:
                break

    def pop_callstack(self, pop_type: PushPopType = None):
        if self.call_stack.current_element.element_type == PushPopType.Function:
            self.trim_whitespace_from_function_end()
        self.call_stack.pop(pop_type)

    def set_chosen_path(self, path: Path):
        self._current_choices.clear()
        new_pointer = self.story.pointer_at_path(path)
        if not new_pointer.is_null and new_pointer.index == -1:
            new_pointer.index = 0
        self.current_pointer = new_pointer
        self.current_turn_index += 1

    def start_function_evaluation_from_game(self, func_container: Container, *arguments):
        self.call_stack.push(PushPopType.FunctionEvaluationFromGame, len(self.evaluation_stack))
        self.call_stack.current_element.current_pointer = Pointer.start_of(func_container)
        self.pass_arguments_to_evaluation_stack(arguments)

    def pass_arguments_to_evaluation_stack(self, *arguments):
        if arguments:
            for argument in arguments:
                if not isinstance(argument, (int, float, str)):
                    raise TypeError("ink arguments when calling EvaluateFunction / ChoosePathStringWithParameters must be int, float or string")
                self.push_evaluation_stack(Value.create(argument))

    def try_exit_function_evaluation_from_game(self) -> bool:
        if self.call_stack.current_element.element_type == PushPopType.FunctionEvaluationFromGame:
            self.current_pointer = Pointer.Null
            self.did_safe_exit = True
            return True
        return False

    def complete_function_evaluation_from_game(self) -> Any:
        if self.call_stack.current_element != PushPopType.FunctionEvaluationFromGame:
            raise StoryException(f"Expected external function evaluation to be complete. Stack trace: {self.call_stack.call_stack}")
        original_evaluation_stack_height = self.call_stack.current_element.evaluation_stack_height_when_pushed
        returned_obj = None
        while len(self.evaluation_stack) > original_evaluation_stack_height:
            popped_obj = self.pop_evaluation_stack()
            if not returned_obj:
                returned_obj = popped_obj
        self.pop_callstack(PushPopType.FunctionEvaluationFromGame)
        if returned_obj:
            if isinstance(returned_obj, Void):
                return None
            if isinstance(returned_obj, Value):
                if returned_obj.value_type == ValueType.DivertTarget:
                    return str(returned_obj.value_object)
                return returned_obj.value_object
        return None

    def add_error(self, message: str, is_warning: bool):
        if not is_warning:
            if not self.current_errors:
                self.current_errors = []
            self.current_errors.append(message)
        else:
            if not self.current_warnings:
                self.current_warnings = []
            self.current_warnings.append(message)

    def output_stream_dirty(self):
        self._output_stream_text_dirty = True
        self._output_stream_tags_dirty = True
