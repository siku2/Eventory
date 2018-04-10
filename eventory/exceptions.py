from typing import Any


class EventoryException(Exception):
    pass


class EventoryParserError(EventoryException):
    pass


class MalformattedEventory(EventoryParserError):
    pass


class EventoryNoParserFound(EventoryParserError, TypeError):
    pass


class EventoryParserHeadError(EventoryParserError):
    pass


class EventoryParserKeyError(EventoryParserHeadError, KeyError):
    def __init__(self, key: str, *args):
        super().__init__(f"{key} is missing!", *args)
        self.key = key


class EventoryParserValueError(EventoryParserHeadError, ValueError):
    def __init__(self, key: str, value: Any, *args):
        super().__init__(f"\"{value}\" for key \"{key}\" is incorrect", *args)
        self.key = key
        self.value = value


class EventoryParserContentError(EventoryParserError):
    pass


class EventorialException(EventoryException):
    pass


class EventoryAlreadyLoaded(EventorialException):
    def __init__(self, eventory: str):
        super().__init__(f"\"{eventory}\" is already loaded!")
