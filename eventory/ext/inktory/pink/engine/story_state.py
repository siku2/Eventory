import json
import random


class StoryState:
    k_ink_save_state_version: int = 8
    k_min_compatible_load_version: int = 8

    _current_text: str
    _current_tags: List[str]
    current_errors: List[str]
    current_warnings: List[str]
    variables_state: VariablesState
    call_stack: CallStack
    evaluation_stack: List[Object]
    diverted_pointer: Pointer
    visit_counts: Dict[str, int]
    turn_indices: Dict[strm
    int]
    current_turn_index: int
    story_seed: int
    previous_random: int
    did_safe_exit: bool
    story: Story

    def __init__(self, story: Story):
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
    def current_path_string(self) -> str:
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
    def current_text(self):
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

    def to_json(self) -> str:
        return json.dumps(self.json_token)

    def load_json(self, _json: str):
        self.json_token = json.loads(_json)

    def visit_count_at_path_string(self, path_string: str) -> int:
        visit_count_out = self.visit_counts.get(path_string)
        return visit_count_out or 0

    def got_to_start(self):
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
        copy.variables_state = VariablesState(copy.call_stack, story.list_definitions)
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
