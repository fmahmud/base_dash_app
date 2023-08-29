import abc
from typing import Dict

from base_dash_app.virtual_objects.interfaces.startable import ExternalTriggerEvent


class Stoppable:
    STOPPABLE_DICT: Dict[ExternalTriggerEvent, list] = {}
    for trigger in ExternalTriggerEvent:
        STOPPABLE_DICT[trigger] = []

    def __init__(self, trigger: ExternalTriggerEvent = ExternalTriggerEvent.HUMAN):
        self.stop_trigger = trigger

    @abc.abstractmethod
    def stop(self, *args, **kwargs):
        pass