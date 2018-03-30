import clr
import subprocess
from os import path
from tempfile import TemporaryDirectory

from System.IO import FileNotFoundException

from eventory import EventoryParser, Eventructor

try:
    clr.AddReference("ink-engine-runtime")
except FileNotFoundException:
    raise FileNotFoundError("Couldn't find \"ink-engine-runtime.dll\", please add it to your PATH or to the CWD in order to use inktory. You can "
                            "download it from here: https://github.com/inkle/ink/releases") from None
else:
    from Ink.Runtime import Story


class InkEventructor(Eventructor):
    def advance(self):
        return


class EventoryInkParser(EventoryParser):

    def parse_content(self, content) -> Story:
        content = EventoryInkParser.compile(content)
        story = Story(content)
        return story

    @staticmethod
    def compile(ink: str) -> str:
        with TemporaryDirectory() as directory:
            in_dir = path.join(directory, "input.ink")
            out_dir = in_dir + ".json"
            with open(in_dir, "w+") as f:
                f.write(ink)
            try:
                subprocess.run(["inklecate", in_dir], check=True)
            except FileNotFoundError:
                raise FileNotFoundError("Couldn't find \"inklecate.exe\", please add it to your PATH or to the CWD in order to use inktory. You can "
                                        "download it from here: https://github.com/inkle/ink/releases") from None
            with open(out_dir, "r", encoding="utf-8-sig") as f:
                data = f.read()
            return data


if __name__ == "__main__":
    parser = EventoryInkParser()
    head, content = parser.load(open("tests/april_fools_day.evory"))
    print(head, content)
