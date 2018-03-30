from typing import Any


class EventoryException(Exception):
    pass


class EventoryParserError(EventoryException):
    pass


class EventoryNoParserFound(EventoryParserError, TypeError):
    pass


class EventoryParserKeyError(EventoryParserError, KeyError):
    def __init__(self, key: str):
        self.key = key


class EventoryParserValueError(EventoryParserError, ValueError):
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value
