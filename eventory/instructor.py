import asyncio
from asyncio import AbstractEventLoop
from concurrent.futures import Executor, ThreadPoolExecutor
from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .eventory import Eventory


class Eventructor:
    def __init__(self, eventory: "Eventory", executor: Executor = None, loop: AbstractEventLoop = None):
        self.eventory = eventory

        self.store = deepcopy(eventory.store)
        self.content = deepcopy(eventory.content)

        self.loop = loop or asyncio.get_event_loop()
        self.executor = executor or ThreadPoolExecutor(3, f"Eventory \"{self.eventory.head.title}\"")

    async def ensure_requirements(self):
        tasks = []
        for requirement in self.eventory.pyrequirements:
            task = asyncio.ensure_future(self.executor.submit(requirement.get))
            tasks.append(task)
        modules = await asyncio.gather(*tasks, loop=self.loop)
        for module in modules:
            self.store[module.__name__] = module

    async def prepare(self):
        await self.ensure_requirements()

    async def advance(self):
        pass
