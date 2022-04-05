import abc
from enum import Enum
from typing import Dict


class ExternalTriggerEvent(Enum):
    SERVER_START = "SERVER_START"
    SERVER_SHUTDOWN = "SERVER_SHUTDOWN"
    NONE = "NONE"


class Startable:
    STARTABLE_DICT: Dict[ExternalTriggerEvent, list] = {
        ExternalTriggerEvent.SERVER_SHUTDOWN: [],
        ExternalTriggerEvent.SERVER_START: [],
        ExternalTriggerEvent.NONE: []
    }

    def __init__(self, trigger: ExternalTriggerEvent = ExternalTriggerEvent.NONE):
        self.start_trigger = trigger
        Startable.STARTABLE_DICT[trigger].append(self)

    @abc.abstractmethod
    def start(self, *args, **kwargs):
        pass


