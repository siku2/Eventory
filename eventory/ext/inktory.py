import clr
import json
import logging
import os
import subprocess
import sys
from os import path
from tempfile import TemporaryDirectory
from typing import Optional

# noinspection PyUnresolvedReferences, PyPackageRequirements
from System.IO import FileNotFoundException

from eventory import EventoryParser, Eventructor, register_parser

try:
    clr.AddReference("ink-engine-runtime")
except FileNotFoundException:
    raise FileNotFoundError(f"Couldn't find \"ink-engine-runtime.dll\", please add it to the CWD ({os.getcwd()}) in order to use inktory. You can "
                            "download it from here: https://github.com/inkle/ink/releases") from None
else:
    # noinspection PyUnresolvedReferences, PyPackageRequirements
    from Ink.Runtime import Story

if sys.platform == "linux":
    INKLECATE_CMD = ["mono", "inklecate.exe"]
else:
    INKLECATE_CMD = ["inklecate.exe"]

log = logging.getLogger(__name__)

try:
    resp = subprocess.run(INKLECATE_CMD, stdout=subprocess.PIPE)
except FileNotFoundError:
    log.warning(
        "Couldn't find \"inklecate.exe\". You won't be able to compile raw ink.\n"
        f"If you wish to use this feature, please add the executable to your PATH or to the CWD ({os.getcwd()}).\n"
        "You can download it from here: https://github.com/inkle/ink/releases"
    )
except OSError:
    log.warning(
        "\"inklecate.exe\" found but it doesn't run!\n"
        f"Make sure you added the correct executable to your PATH or to the CWD ({os.getcwd()}).\n"
        "You can download the executable from here: https://github.com/inkle/ink/releases"
    )
else:
    if "Usage: inklecate" in resp.stdout.decode("utf-8"):
        log.info("\"inklecate.exe\" passed check!")
    else:
        log.warning("Found \"inklecate.exe\" but it's not responding properly. Compiling raw ink might not work")


class EventoryInkContent:
    def __init__(self, raw: Optional[str], compiled: str):
        self.raw = raw
        self.compiled = compiled

    def __repr__(self):
        content_str = "raw, compiled" if self.raw else "compiled"
        return f"<InkContent [{content_str}]>"

    def __str__(self):
        return self.raw or self.compiled


class InkEventructor(Eventructor):
    story: Story
    content: EventoryInkContent

    def init(self):
        self.story = Story(self.content.compiled)

    async def index_input(self, max_index: int) -> int:
        while True:
            inp = await self.narrator.input()
            inp = inp.strip()
            if inp.isnumeric():
                num = int(inp)
                if 0 < num <= max_index:
                    return num - 1
            await self.narrator.output(f"Please use a number between 1 and {max_index}\n")

    async def play(self):
        await self.prepare()
        while True:
            while self.story.canContinue:
                out = self.story.Continue()
                await self.narrator.output(out)

            if self.story.currentChoices.Count > 0:
                out = "\n".join(f"{i}. {choice.text}" for i, choice in enumerate(self.story.currentChoices, 1)) + "\n"
                await self.narrator.output(out)
                index = await self.index_input(self.story.currentChoices.Count)
                self.story.ChooseChoiceIndex(index)
            else:
                break


class EventoryInkParser(EventoryParser):
    instructor = InkEventructor

    @staticmethod
    def parse_content(content: str) -> EventoryInkContent:
        try:
            # check if it's already compiled
            json.loads(content)
        except json.JSONDecodeError:
            # if not, compile it
            log.debug("Content needs to be compiled")
            raw = content
            compiled = EventoryInkParser.compile(content)
        else:
            log.debug("Content provided as JSON")
            raw = None
            compiled = content

        return EventoryInkContent(raw, compiled)

    @staticmethod
    def compile(ink: str) -> str:
        with TemporaryDirectory() as directory:
            in_dir = path.join(directory, "input.ink")
            out_dir = in_dir + ".json"
            with open(in_dir, "w+") as f:
                f.write(ink)
            try:
                subprocess.run([*INKLECATE_CMD, in_dir], check=True)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Couldn't find \"inklecate.exe\", please add it to your PATH or to the CWD ({os.getcwd()}) in order to compile ink. You can "
                    "download it from here: https://github.com/inkle/ink/releases") from None
            with open(out_dir, "r", encoding="utf-8-sig") as f:
                data = f.read()
            return data


register_parser(EventoryInkParser, ("Ink",))
