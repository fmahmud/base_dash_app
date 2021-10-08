import abc
from typing import Dict

from utils.Startable import ExternalTriggerEvent


class Stoppable:
    STOPPABLE_DICT: Dict[ExternalTriggerEvent, list] = {}
    for trigger in ExternalTriggerEvent:
        STOPPABLE_DICT[trigger] = []

    def __init__(self, trigger: ExternalTriggerEvent = ExternalTriggerEvent.NONE):
        self.stop_trigger = trigger

    @abc.abstractmethod
    def stop(self):
        pass