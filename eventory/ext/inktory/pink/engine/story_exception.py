class StoryException(Exception):
    use_end_line_number: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
