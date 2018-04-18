from .object import Object


class Tag(Object):
    text: str

    def __init__(self, tag_text: str):
        super().__init__()
        self.text = tag_text

    def __str__(self):
        return f"# {self.text}"
