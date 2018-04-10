"""This module contains the Eventructor."""

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

    If you think of the Eventory as the CD, the Eventructor is the player and the Eventarrator is the speakers.

    Args:
        eventory: Eventory to play
        narrator: Eventarrator to play to
        executor: Specify if you wish to use a special kind of executor.
        loop: Loop to use for async operations

    Attributes:
        eventory (Eventory): Eventory to play
        narrator (Eventarrator): Eventarrator to play to
        executor (Executor): Specify if you wish to use a special kind of executor.
        loop (AbstractEventLoop): Loop to use for async operations
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
    def stopped(self) -> bool:
        """Indication whether the Eventory is still running."""
        return getattr(self, "_stopped", False)

    def init(self):
        """This method is called right after initialisation.

        This method only serves as a convenience to avoid having to call super().__init__ because it looks ugly.
        """
        pass

    def serialise(self) -> str:
        """Serialise the current state of the Eventructor.

        Returns:
            str: Current state
        """
        raise NotImplementedError

    @classmethod
    def serialise_content(cls, content: Any) -> str:
        """Serialise the content of an Eventory.

        Args:
            content: Content to serialise

        Returns:
            str: Serialised content
        """
        return str(content)

    async def ensure_requirements(self):
        """Makes sure that all requirements are present and loaded."""
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
        """Prepare the Eventructor to play the Eventory."""
        log.debug(f"{self} preparing")
        await self.ensure_requirements()
        log.debug(f"{self} all set!")

    async def play(self):
        """Play this story."""
        raise NotImplementedError
