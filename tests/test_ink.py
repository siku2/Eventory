import asyncio

import pytest

import eventory


@pytest.mark.asyncio
async def test__intercept():
    eventory.load_ext("inktory")
    with open("tests/the_intercept.evory", "r") as f:
        story = eventory.load(f)
    narrator = eventory.StreamEventarrator()
    instructor = story.narrate(narrator)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test__intercept())
