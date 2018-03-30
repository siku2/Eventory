from .__version__ import __author__, __description__, __license__, __title__, __url__, __version__
from .eventorial import Eventorial
from .eventory import Eventory
from .exceptions import EventoryException, EventoryParserError, EventoryParserKeyError
from .instructor import Eventructor
from .narrator import DiscordEventarrator, StreamEventarrator
from .parser import EventoryParser


def load(stream):
    pass