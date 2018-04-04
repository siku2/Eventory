import pytest

import eventory


@pytest.mark.asyncio
async def test__intercept():
    eventory.load_ext("inktory")
    with open("tests/the_intercept.evory", "r") as f:
        story = eventory.load(f)
    assert story.title == "The Intercept"
