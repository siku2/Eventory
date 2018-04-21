import time
from typing import Dict, List, Tuple

from .call_stack import CallStack
from .control_command import ControlCommand
from .object import Object
from .utils import groupby


class ProfileNode:
    key: str
    open_in_ui: bool
    _nodes: Dict[str, "ProfileNode"]
    _self_millisecs: float
    _total_millisecs: float
    _self_sample_count: int
    _total_sample_count: int

    def __init__(self, key: str = None):
        self.open_in_ui = False
        self._nodes = {}
        self._self_millisecs = 0
        self._total_millisecs = 0
        self._self_sample_count = 0
        self._total_sample_count = 0
        self.key = key

    def __str__(self) -> str:
        return self.print_hierarchy(0)

    @property
    def has_children(self) -> bool:
        return self._nodes and len(self._nodes) > 0

    @property
    def total_millisecs(self) -> int:
        return int(self._total_millisecs)

    @property
    def descending_ordered_nodes(self) -> List[Tuple[str, "ProfileNode"]]:
        if not self._nodes:
            return []
        ordered: List[Tuple[str, "ProfileNode"]] = sorted(map(tuple, self._nodes.items()), key=lambda item: item[1]._total_millisecs)
        return ordered

    @property
    def own_report(self) -> str:
        return f"total {self._total_millisecs}, self {self._self_millisecs} " \
               f"({self._self_sample_count} self samples, {self._total_sample_count} total)"

    def add_sample(self, stack: List[str], stack_idx: int, duration: float):
        self._total_sample_count += 1
        self._total_millisecs += duration
        if stack_idx == len(stack) - 1:
            self._self_sample_count += 1
            self._self_millisecs += duration
        if stack_idx + 1 < len(stack):
            self.add_sample_to_node(stack, stack_idx + 1, duration)

    def add_sample_to_node(self, stack: List[str], stack_idx: int, duration: float):
        node_key = stack[stack_idx]
        if not self._nodes:
            self._nodes = {}
        node = self._nodes.get(node_key)
        if not node:
            node = ProfileNode(node_key)
            self._nodes[node_key] = node
        node.add_sample(stack, stack_idx, duration)

    def print_hierarchy(self, indent: int) -> str:
        pad = indent * " "
        sb = f"{pad}{self.key}: {self.own_report}\n"
        if not self._nodes:
            return sb
        for key, value in self.descending_ordered_nodes:
            sb += value.print_hierarchy(indent + 1)
        return sb


class Stopwatch:
    """Just me mocking the c# implementation of a "Stopwatch" with a few lines of python code"""
    start_time: float
    elapsed_time: float

    def __init__(self):
        self.start_time = time.time()
        self.elapsed_time = 0

    @property
    def milliseconds(self) -> float:
        return 1000 * self.elapsed_time

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.elapsed_time += time.time() - self.start_time

    def reset(self):
        self.start_time = time.time()
        self.elapsed_time = 0


class StepDetails:
    step_type: str
    obj: Object
    time: float

    def __init__(self, step_type: str, obj: Object):
        self.step_type = step_type
        self.obj = obj
        self.time = 0


class Profiler:
    _continue_watch: Stopwatch
    _step_watch: Stopwatch
    _snap_watch: Stopwatch

    _continue_total: float
    _snap_total: float
    _step_total: float
    _curr_step_stack: List[str]
    _curr_step_details: StepDetails
    _rootNode: ProfileNode
    _num_continues: int
    _step_details: List[StepDetails]

    def __init__(self):
        self._root_node = ProfileNode()

    @property
    def root_node(self):
        return self._root_node

    def report(self) -> str:
        return f"{self._num_continues} CONTINUES / LINES:\n" \
               f"TOTAL TIME: {self.format_millisecs(self._continue_total)}\n" \
               f"SNAPSHOTTING: {self.format_millisecs(self._snap_total)}\n" \
               f"OTHER: {self.format_millisecs(self._continue_total - (self._step_total + self._snap_total))}\n" \
               f"{self._root_node}"

    def pre_continue(self):
        self._continue_watch.reset()
        self._continue_watch.start()

    def post_contine(self):
        self._continue_watch.stop()
        self._continue_total += self.millisecs(self._continue_watch)
        self._num_continues += 1

    def pre_step(self):
        self._curr_step_stack = None
        self._step_watch.reset()
        self._step_watch.start()

    def step(self, callstack: CallStack):
        self._step_watch.stop()
        stack = []
        for i in range(len(callstack.elements)):
            obj_path = callstack.elements[i].current_pointer.path
            stack_element_name = ""

            for c in range(len(obj_path)):
                comp = obj_path.get_component(c)
                if not comp.is_index:
                    stack_element_name = comp.name
                    break
            stack.append(stack_element_name)
        self._curr_step_stack = stack
        curr_obj = callstack.current_element.current_pointer.resolve()
        if isinstance(curr_obj, ControlCommand):
            step_type = f"{curr_obj.command_type} CC"
        else:
            step_type = type(curr_obj).__name__
        self._curr_step_details = StepDetails(step_type, curr_obj)
        self._step_watch.start()

    def post_step(self):
        self._step_watch.stop()
        duration = self.millisecs(self._step_watch)
        self._step_total += duration
        self._root_node.add_sample(self._curr_step_stack, -1, duration)
        self._curr_step_details.time = duration
        self._step_details.append(self._curr_step_details)

    def step_length_report(self) -> str:
        sb = f"TOTAL: {self._root_node.total_millisecs}ms\n"

        average_step_times = ", ".join([
            f"{name}: {time}ms" for name, time in
            sorted(
                (
                    (f"{key} (x{len(values)})", sum(v.time for v in values) / len(values)) for key, values in
                    groupby(self._step_details, lambda step: step.step_type)
                ),
                key=lambda item: item[1]
            )
        ])
        sb += f"AVERAGE STEP TIMES: {average_step_times}"

        accum_step_times = ", ".join([
            f"{name}: {time}ms" for name, time in
            sorted(
                (
                    (f"{key} (x{len(values)})", sum(v.time for v in values)) for key, values in
                    groupby(self._step_details, lambda step: step.step_type)
                ),
                key=lambda item: item[1]
            )
        ])
        sb += f"ACCUMULATED STEP TIMES: {accum_step_times}"
        return sb

    def megalog(self) -> str:
        sb = "Step type\t Description\t Path\t Time\n"
        for step in self._step_details:
            sb += f"{step.type}\t{step.obj}\t{step.obj.path}\t{step.time}\n"
        return sb

    def pre_snapshot(self):
        self._snap_watch.reset()
        self._snap_watch.start()

    def post_snapshot(self):
        self._snap_watch.stop()
        self._snap_total += self.millisecs(self._snap_watch)

    def millisecs(self, watch: Stopwatch) -> float:
        """This function is ridiculous xD"""
        return watch.milliseconds

    def format_millisecs(self, num: float) -> str:
        if num > 5000:
            return f"{num / 1000:.0} secs"
        elif num > 1000:
            return f"{num / 1000:.1} secs"
        elif num > 100:
            return f"{num:.0} ms"
        elif num > 1:
            return f"{num: .1} ms"
        elif num > .01:
            return f"{num:.3} ms"
        else:
            return f"{num} ms"
