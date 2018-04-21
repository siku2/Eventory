import importlib
from collections import defaultdict
from typing import Any, Callable, Iterable, List, Tuple, TypeVar


def remove_range_from_list(l: list, start: int, end: int):
    start = start if start >= 0 else len(l) + start
    end = end if end >= 0 else len(l) + end
    if start > end:
        start, end = end, start
    for i in range(end - 1, start - 1, -1):
        l.pop(i)


def late_import_from(package: str, item: str, *, parent: str = None) -> Any:
    parent = parent or __package__
    return getattr(importlib.import_module(package, package=parent), item)


T = TypeVar("T")
I = TypeVar("I")


def groupby(l: Iterable[T], key: Callable[[T], I]) -> List[Tuple[I, List[T]]]:
    d = defaultdict(list)
    for item in l:
        d[key(item)].append(item)
    return list(d.items())
