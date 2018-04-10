import asyncio
import logging
from asyncio import AbstractEventLoop
from concurrent.futures import Executor, ThreadPoolExecutor
from copy import deepcopy
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .eventory import Eventory
    from .narrator import Eventarrator

log = logging.getLogger(__name__)


class Eventructor:
    """The Eventructor "plays" an Eventory to a Eventarrator.

    If you think of the Eventory as the CD, the Eventructor is the player and the Eventarrator is the speakers
    """

    def __init__(self, eventory: "Eventory", narrator: "Eventarrator", *, executor: Executor = None, loop: AbstractEventLoop = None):
        self.eventory = eventory
        self.narrator = narrator

        self.store = deepcopy(eventory.store)

        self.loop = loop or asyncio.get_event_loop()
        self.executor = executor or ThreadPoolExecutor(3, f"Eventory \"{self.title}\"")
        self.init()

    def __getattr__(self, item):
        return getattr(self.eventory, item)

    @property
    def stopped(self):
        return getattr(self, "_stopped", False)

    def init(self):
        pass

    def serialise(self) -> str:
        raise NotImplementedError

    @classmethod
    def serialise_content(cls, content: Any) -> str:
        return str(content)

    async def ensure_requirements(self):
        if self.global_store.get("_requirements_met"):
            log.debug("requirements already met (\"_requirements_met\" flag is set)")
            return

        tasks = []
        for requirement in self.requirements:
            fut = self.loop.run_in_executor(self.executor, requirement.get)
            task = asyncio.ensure_future(fut)
            tasks.append(task)
        modules = await asyncio.gather(*tasks, loop=self.loop)
        for module in modules:
            self.global_store[module.__name__] = module

        self.global_store["_requirements_met"] = True

    async def prepare(self):
        log.debug(f"{self} preparing")
        await self.ensure_requirements()
        log.debug(f"{self} all set!")

    async def play(self):
        raise NotImplementedError
