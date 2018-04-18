from .path import Path
from .push_pop import PushPopType
from .story_exception import StoryException


class Element:
    def __init__(self, element_type, container, content_index, in_expression_evaluation=False):
        self.current_container = container
        self.current_content_index = content_index
        self.in_expression_evaluation = in_expression_evaluation
        self.temporary_variables = {}
        self.element_type = element_type
        self.evaluation_stack_height_when_pushed = 0

    @property
    def current_object(self):
        if self.current_container and self.current_content_index < len(self.current_container.content):
            return self.current_container.content[self.current_content_index]

    @current_object.setter
    def current_object(self, value):
        if not value:
            self.current_container = None
            self.current_content_index = 0
            return
        self.current_container = value.parent
        if self.current_container:
            self.current_content_index = self.current_container.content.index(value)
        if self.current_container or self.current_content_index == -1:
            self.current_container = value
            self.current_content_index = 0

    def copy(self) -> "Element":
        copy = Element(self.element_type, self.current_container, self.current_content_index, self.in_expression_evaluation)
        copy.temporary_variables = self.temporary_variables.copy()
        copy.evaluation_stack_height_when_pushed = self.evaluation_stack_height_when_pushed
        return copy


class Thread:
    def __init__(self, j_thread_obj=None, story_context=None):
        self.callstack = []
        self.previous_content_object = None
        if not all((j_thread_obj, story_context)):
            self.thread_index = None
            self.j_thread_callstack = None
            return
        self.thread_index = j_thread_obj["thread_index"]
        self.j_thread_callstack = j_thread_obj["callstack"]
        for j_element_obj in self.j_thread_callstack:
            push_pop_type = j_element_obj["type"]  # TODO: convert to PushPopType Enum
            current_container = None
            content_index = 0
            current_container_path_str_token = j_element_obj.get("c_path")
            if current_container_path_str_token:
                current_container_path_str = str(current_container_path_str_token)
                current_container = story_context.content_at_path(Path(current_container_path_str))
                content_index = j_element_obj["idx"]
            in_expression_evaluation = j_element_obj["exp"]
            el = Element(push_pop_type, current_container, content_index, in_expression_evaluation)
            j_obj_temps = j_element_obj["temp"]
            el.temporary_variables = j_obj_temps
            self.callstack.append(el)

        prev_content_obj_path = j_thread_obj.get("previous_content_object")
        if prev_content_obj_path:
            prev_path = Path(prev_content_obj_path)
            self.previous_content_object = story_context.content_at_path(prev_path)

    def copy(self):
        copy = Thread()
        copy.thread_index = self.thread_index
        for e in self.callstack:
            copy.callstack.append(e.copy())
        copy.previous_content_object = self.previous_content_object
        return copy

    @property
    def json_token(self):
        thread_j_obj = {}
        j_thread_callstack = []
        for el in self.callstack:
            j_obj = {}
            if el.current_container:
                j_obj["c_path"] = el.current_container.path.components_string
                j_obj["idx"] = el.current_content_index
            j_obj["exp"] = el.in_expression_evaluation
            j_obj["type"] = el.element_type
            j_obj["temp"] = el.temporary_variables
            j_thread_callstack.append(j_obj)
        thread_j_obj["callstack"] = j_thread_callstack
        thread_j_obj["thread_index"] = self.thread_index
        if self.previous_content_object:
            thread_j_obj["previous_content_object"] = str(self.previous_content_object.path)
        return thread_j_obj


class CallStack:
    def __init__(self, root_content_container):
        self._threads = []
        self._thread_counter = 0
        if isinstance(root_content_container, CallStack):
            for other_thread in root_content_container._threads:
                self._threads.append(other_thread.copy())
        else:
            self._threads.append(Thread())
            self._threads[0].call_stack.append(Element(PushPopType.Tunnel, root_content_container, 0))

    @property
    def elements(self):
        return self.call_stack

    @property
    def depth(self):
        return len(self.elements)

    @property
    def current_element(self):
        return self.call_stack[-1]

    @property
    def current_element_index(self):
        return len(self.call_stack) - 1

    @property
    def current_thread(self):
        return self._threads[-1]

    @current_thread.setter
    def current_thread(self, value):
        self._threads.clear()
        self._threads.append(value)

    @property
    def call_stack(self):
        return self.current_thread.callstack

    @property
    def can_pop(self):
        return len(self.call_stack) > 1

    @property
    def element_is_evaluate_from_game(self):
        return self.current_element.element_type == PushPopType.FunctionEvaluationFromGame

    @property
    def can_pop_thread(self):
        return len(self.call_stack) > 1 and not self.element_is_evaluate_from_game

    @property
    def call_stack_trace(self):
        sb = ""
        for t, thread in enumerate(self._threads):
            is_current = t == len(self._threads) - 1
            sb += "=== THREAD {0}/{1} {2}===\n".format(t + 1, len(self._threads), "(current) " if is_current else "")

            for i, item in enumerate(thread.callstack):
                if item.element_type == PushPopType.Function:
                    sb += "  [FUNCTION] "
                else:
                    sb += "  [TUNNEL] "

                obj = item.current_object
                if not obj:
                    if item.current_container:
                        sb += "<SOMEWHERE IN {0}>\n".format(item.current_container.path)
                    else:
                        sb += "<UNKNOWN STACK ELEMENT>\n"
                else:
                    sb += "{0}\n".format(obj.path)
        return sb

    def set_json_token(self, j_object, story_context):
        self._threads.clear()
        j_threads = j_object["threads"]
        for j_thread_obj in j_threads:
            thread = Thread(j_thread_obj, story_context)
            self._threads.append(thread)
        self._thread_counter = j_object["thread_counter"]

    def get_json_token(self):
        j_object = {}
        j_threads = []
        for thread in self._threads:
            j_threads.append(thread.json_token)

        j_object["threads"] = j_threads
        j_object["thread_counter"] = self._thread_counter
        return j_object

    def push_thread(self):
        new_thread = self.current_thread.copy()
        self._thread_counter += 1
        new_thread.thread_index = self._thread_counter
        self._threads.append(new_thread)

    def pop_thread(self):
        if self.can_pop_thread:
            self._threads.remove(self.current_thread)
        else:
            raise IndexError("Can't pop thread")

    def push(self, _type, external_evaluation_stack_height=0):
        element = Element(_type, self.current_element.current_container, self.current_element.current_content_index, in_expression_evaluation=False)
        element.evaluation_stack_height_when_pushed = external_evaluation_stack_height
        self.call_stack.append(element)

    def can_pop_type(self, _type=None):
        if not self.can_pop:
            return False
        if _type is None:
            return True

        return self.current_element.element_type == _type

    def pop(self, _type=None):
        if self.can_pop_type(_type):
            self.call_stack.pop()
        else:
            raise ValueError("Mismatched push/pop in Callstack")

    def get_temporary_variable_with_name(self, name, context_index=-1):
        if context_index == -1:
            context_index = self.current_element_index + 1

        context_element = self.call_stack[context_index - 1]

        return context_element.temporary_variables.get(name)

    def set_temporary_variable(self, name, value, declare_new, context_index=-1):
        if context_index == -1:
            context_index = self.current_element_index + 1

        context_element = self.call_stack[context_index - 1]

        if not declare_new and name not in context_element.temporary_variables:
            raise StoryException("Could not find temporary variable to set: " + name)

        old_value = context_element.temporary_variables.get(name)
        if old_value:
            pass  # TODO: https://github.com/inkle/ink/blob/master/ink-engine-runtime/CallStack.cs#L345
        context_element.temporary_variables[name] = value

    def context_for_variable_named(self, name):
        if name in self.current_element.temporary_variables:
            return self.current_element_index + 1
        else:
            return 0

    def thread_with_index(self, index):
        return next(thread for thread in self._threads if thread.thread_index == index)
