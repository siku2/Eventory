import pytest

import eventory
from eventory import Eventorial

eventory.load_ext("inktory")


@pytest.mark.asyncio
async def test_eventorial():
    eventorial = Eventorial()
    with open("tests/the_intercept.evory", "r") as f:
        eventorial.add(f)
    await eventorial.load("https://raw.githubusercontent.com/siku2/Eventory/master/tests/the_intercept.evory")
    assert len(eventorial.eventories) == 2
