"""This module contains all exceptions raised by Eventory."""

from typing import Any


class EventoryException(Exception):
    """A generic exception.

    In theory all exceptions raised by Eventory should derive from this Exception.
    """
    pass


class EventoryParserError(EventoryException):
    """All exceptions based on parsing an Eventory derive from this class."""
    pass


class MalformattedEventory(EventoryParserError):
    """When trying to load an Eventory that is in some way malformatted."""
    pass


class EventoryNoParserFound(EventoryParserError, TypeError):
    """When there's no available parser that could parse an Eventory."""
    pass


class EventoryParserHeadError(EventoryParserError):
    """When there's something wrong with the head of an Eventory."""
    pass


class EventoryParserKeyError(EventoryParserHeadError, KeyError):
    """When there's a key missing in the head of an Eventory."""

    def __init__(self, key: str, *args):
        super().__init__(f"{key} is missing!", *args)
        self.key = key


class EventoryParserValueError(EventoryParserHeadError, ValueError):
    """When a key is present, but the value isn't valid in the head of an Eventory."""

    def __init__(self, key: str, value: Any, *args):
        super().__init__(f"\"{value}\" for key \"{key}\" is incorrect", *args)
        self.key = key
        self.value = value


class EventoryParserContentError(EventoryParserError):
    """For Errors concerning the content of an Eventory"""
    pass


class EventorialException(EventoryException):
    """For all kinds of errors in an Eventorial"""
    pass


class EventoryAlreadyLoaded(EventorialException):
    """When an Eventory is already present in an Eventorial."""

    def __init__(self, eventory: str):
        super().__init__(f"\"{eventory}\" is already loaded!")
