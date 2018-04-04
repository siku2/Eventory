import clr
import os
import subprocess
import sys
from os import path
from tempfile import TemporaryDirectory

from System.IO import FileNotFoundException

from eventory import EventoryParser, Eventructor, register_parser

try:
    clr.AddReference("ink-engine-runtime")
except FileNotFoundException:
    raise FileNotFoundError(f"Couldn't find \"ink-engine-runtime.dll\", please add it to the CWD ({os.getcwd()}) in order to use inktory. You can "
                            "download it from here: https://github.com/inkle/ink/releases") from None
else:
    from Ink.Runtime import Story

if sys.platform == "linux":
    INKLECATE_CMD = ["mono", "inklecate.exe"]
else:
    INKLECATE_CMD = ["inklecate.exe"]


class InkEventructor(Eventructor):
    def init(self):
        self.story = Story(self.content)

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
        story = self.story
        while True:
            while story.canContinue:
                out = story.Continue()
                await self.narrator.output(out)

            if story.currentChoices.Count > 0:
                out = "\n".join(f"{i}. {choice.text}" for i, choice in enumerate(story.currentChoices, 1)) + "\n"
                await self.narrator.output(out)
                index = await self.index_input(story.currentChoices.Count)
                story.ChooseChoiceIndex(index)
            else:
                break


class EventoryInkParser(EventoryParser):
    instructor = InkEventructor

    @staticmethod
    def parse_content(content) -> Story:
        content = EventoryInkParser.compile(content)
        return content

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
                    f"Couldn't find \"inklecate.exe\", please add it to your PATH or to the CWD ({os.getcwd()}) in order to use inktory. You can "
                    "download it from here: https://github.com/inkle/ink/releases") from None
            with open(out_dir, "r", encoding="utf-8-sig") as f:
                data = f.read()
            return data


register_parser(EventoryInkParser, ("Ink",))
