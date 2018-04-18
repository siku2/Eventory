from .call_stack import Thread
from .object import Object
from .path import Path


class Choice(Object):
    text: str
    index: int
    source_path: str
    target_path: Path
    thread_at_generation: Thread
    original_thread_index: int
    is_invisible_default: bool

    def __init__(self):
        super().__init__()
        self.text = ""
        self.source_path = ""
        self.index = 0
        self.target_path = None
        self.thread_at_generation = None
        self.original_thread_index = 0
        self.is_invisible_default = False

    @property
    def path_string_on_choice(self) -> str:
        return str(self.target_path)

    @path_string_on_choice.setter
    def path_string_on_choice(self, value: str):
        self.target_path = Path(value)
