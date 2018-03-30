import abc


class Eventarrator(metaclass=abc.ABCMeta):
    """There he goes again with the Eventory + narrator combination. Are you sick of it yet?"""

    def __init__(self):
        pass


class StreamEventarrator(Eventarrator):
    pass


class DiscordEventarrator(Eventarrator):
    pass
