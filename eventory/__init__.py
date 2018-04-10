import importlib
import logging

from .__version__ import __author__, __description__, __license__, __title__, __url__, __version__
from .eventorial import Eventorial, get_eventory
from .eventory import Eventory, EventoryMeta
from .exceptions import *
from .instructor import Eventructor
from .narrator import Eventarrator, StreamEventarrator
from .parser import Eventoriment, EventoryParser, load, register_parser

log = logging.getLogger(__name__)


def load_ext(ext: str):
    """Load an extension. This can be used to activate the Ink parser in order to load Inktory Eventories.

    Args:
        ext (str): The name of the extension to load (i.e. "inktory").
    """
    importlib.import_module(f"eventory.ext.{ext}", "eventory")
    log.info(f"loaded extension {ext}")
