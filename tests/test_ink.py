import asyncio

import eventory
from eventory import Eventoriment


async def run_intercept():
    eventory.load_ext("inktory")
    with open("tests/the_intercept.evory", "r") as f:
        story = eventory.load(f)
        story.meta.requirements = [Eventoriment("requests")]
        narrator = eventory.StreamEventarrator()
        instructor = story.narrate(narrator)
        await instructor.play()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_intercept())
