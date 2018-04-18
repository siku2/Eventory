class DebugMetadata:
    start_line_number: int
    end_line_number: int
    file_name: str
    source_name: str

    def __init__(self):
        self.start_line_number = 0
        self.end_line_number = 0
        self.file_name = None
        self.source_name = None

    def __str__(self):
        if self.file_name:
            return f"line {self.start_line_number} of {self.file_name}"
        else:
            return f"line {self.start_line_number}"
