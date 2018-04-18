from enum import IntEnum, auto

from .object import Object


class CommandType(IntEnum):
    NotSet = -1,
    EvalStart = auto
    EvalOutput = auto
    EvalEnd = auto
    Duplicate = auto
    PopEvaluatedValue = auto
    PopFunction = auto
    PopTunnel = auto
    BeginString = auto
    EndString = auto
    NoOp = auto
    ChoiceCount = auto
    TurnsSince = auto
    ReadCount = auto
    Random = auto
    SeedRandom = auto
    VisitIndex = auto
    SequenceShuffleIndex = auto
    StartThread = auto
    Done = auto
    End = auto
    ListFromInt = auto
    ListRange = auto
    TOTAL_VALUES = auto


class ControlCommandMeta(type):
    def __getattr__(self, item):
        if isinstance(item, str):
            if item in CommandType:
                return ControlCommand(CommandType[item])
        raise AttributeError


class ControlCommand(Object, metaclass=ControlCommandMeta):
    command_type: CommandType

    def __init__(self, command_type: CommandType = CommandType.NotSet):
        super().__init__()
        self.command_type = command_type

    def __str__(self):
        return str(self.command_type)

    def copy(self) -> "ControlCommand":
        return ControlCommand(self.command_type)
