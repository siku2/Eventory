import importlib

from .__version__ import __author__, __description__, __license__, __title__, __url__, __version__
from .eventorial import Eventorial
from .eventory import Eventory, EventoryMeta
from .exceptions import EventoryException, EventoryNoParserFound, EventoryParserError, EventoryParserKeyError
from .instructor import Eventructor
from .narrator import Eventarrator, StreamEventarrator
from .parser import Eventoriment, EventoryParser, load, register_parser


def load_ext(ext: str):
    """Load an extension. This can be used to activate the Ink parser in order to load Inktory Eventories"""
    importlib.import_module(f"eventory.ext.{ext}", "eventory")
