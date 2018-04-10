from os import path
import shutil

import pytest

import eventory
from eventory import Eventorial
from tempfile import TemporaryDirectory

eventory.load_ext("inktory")


@pytest.mark.asyncio
async def test_eventorial():
    eventorial = Eventorial()
    await eventorial.load("https://raw.githubusercontent.com/siku2/Eventory/master/tests/the_intercept.evory")
    story = eventorial["The Intercept"]
    assert story
    loc = path.join(eventorial.directory, story.filename)
    assert path.isfile(loc)
    del eventorial
    assert not path.isfile(loc)


@pytest.mark.asyncio
async def test_preload():
    with TemporaryDirectory() as directory:
        shutil.copy("tests/crime_scene.evory", path.join(directory, "crime_scene.evory"))
        eventorial = Eventorial(directory)
        assert eventorial["Crime Scene"]