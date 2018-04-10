"""Eventory.

Attributes:
    FILENAME_REGEX (Pattern): Regex to match everything that's not suited for filenames in order to replace it.
"""

import re
from io import TextIOBase
from typing import Any, Dict, Sequence, TYPE_CHECKING, Type, Union

import yaml

from . import constants

if TYPE_CHECKING:
    from .parser import Eventoriment
    from .instructor import Eventructor
    from .narrator import Eventarrator

FILENAME_REGEX = re.compile(r"[\W_]+")


class EventoryMeta:
    """Information for an Eventory.

    Args:
        title: Title of the Eventory
        description: Description of the Eventory
        version: Version of the Eventory
        author: Name of the author of the Eventory
        requirements: List of requirements needed to run the Eventory

    Attributes:
        title
        description
        version
        author
        requirements
    """

    def __init__(self, title: str, description: str, version: int, author: str, requirements: Sequence["Eventoriment"]):
        self.title = title
        self.description = description
        self.version = version
        self.author = author

        self.requirements = requirements

    def __repr__(self) -> str:
        return f"\"{self.title}\" - {self.author} ({self.version})"

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary containing all the information of this instance.

        Returns:
            dict: Dictionary representing the instance
        """
        data = vars(self)
        data["requirements"] = [req.to_dict() for req in data["requirements"]]
        return data

    def serialise(self) -> str:
        """Serialise the information into YAML.

        Returns:
            str: YAML data representing the information
        """
        return yaml.dump(self.to_dict())


class Eventory:
    """An Eventory story.

    Note:
        You shouldn't create these yourself. Eventories should be created by an EventoryParser.

    Instead of calling "eventory.meta.title" you can also use "eventory.title". All attributes of EventoryMeta are available from the Eventory.

    Args:
        meta: Meta object for the Eventory
        content: Actual content that will be used by the Eventructor
        eventructor_cls: Eventructor type that should be used to instruct this Eventory
        store: Default store that will be passed to the Eventructor
        global_store: Global store of the Eventory

    Attributes:
        meta (EventoryMeta): Meta object for the Eventory
        content (Any): Actual content that will be used by the Eventructor
        eventructor_cls (Type[Eventructor]): Eventructor type that should be used to instruct this Eventory
        store (dict): Default store that will be passed to the Eventructor
        global_store (dict): Global store of the Eventory

    """

    def __init__(self, meta: EventoryMeta, content: Any, eventructor_cls: Type["Eventructor"], *, store: dict = None, global_store: dict = None):
        self.meta = meta
        self.content = content
        self.eventructor_cls = eventructor_cls

        self.store = store or {}
        self.global_store = global_store or {}

    def __repr__(self) -> str:
        return f"{self.meta}: {self.eventructor_cls}"

    def __getattr__(self, item) -> Any:
        return getattr(self.meta, item)

    @property
    def filename(self) -> str:
        """A filename made from the title of the Eventory."""
        title = FILENAME_REGEX.sub("_", self.title.lower())
        return f"{title}{constants.FILE_SUFFIX}"

    def narrate(self, eventarrator: "Eventarrator", **kwargs) -> "Eventructor":
        """Get an Eventructor to instruct this Eventory.

        This is just a convenience wrapper for::

            eventory.eventructor_cls(eventory, eventarrator, **kwargs)

        Args:
            eventarrator: Eventarrator to use

        Returns:
            Eventructor: An Eventructor loaded with this Eventory ready to play it.
        """
        return self.eventructor_cls(self, eventarrator, **kwargs)

    def serialise(self) -> str:
        """Serialise this Eventory into a string.

        The resulting string can be used to reconstruct the same Eventory.

        Returns:
            str: Serialised Eventory
        """
        head = self.meta.serialise()
        content = self.eventructor_cls.serialise_content(self.content)
        return f"---\n{head}\n---\n\n{content}"

    def save(self, fp: Union[str, TextIOBase] = None) -> TextIOBase:
        """Save this Eventory to disk.

        Args:
            fp: The location to save to. If the location is provided as a string it'll be formatted with filename=self.filename
                so you may use {filename} and it will be replaced with the actual filename.

        Returns:
            TextIOBase: The object that was written to
        """
        if not fp:
            fp = self.filename

        if isinstance(fp, str):
            fp = fp.format(filename=self.filename)
            with open(fp, "w+", encoding="utf-8") as f:
                return self.save(f)

        data = self.serialise()
        fp.write(data)
        return fp
