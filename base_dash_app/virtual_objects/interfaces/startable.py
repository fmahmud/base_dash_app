import abc
from enum import Enum
from typing import Dict, List

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.nameable import Nameable


class ExternalTriggerEvent(Enum):
    SERVER_START = "SERVER_START"
    SERVER_SHUTDOWN = "SERVER_SHUTDOWN"
    SCHEDULED = "SCHEDULED"
    HUMAN = "NONE"
    NONE = "NONE"


class Startable:
    STARTABLE_DICT: Dict[ExternalTriggerEvent, List['Startable']] = {
        e: [] for e in ExternalTriggerEvent
    }

    def __init__(self, trigger: ExternalTriggerEvent = ExternalTriggerEvent.HUMAN):
        self.start_trigger = trigger
        Startable.STARTABLE_DICT[trigger].append(self)

    @abc.abstractmethod
    def get_start_time(self):
        pass

    @abc.abstractmethod
    def get_end_time(self):
        pass

    @abc.abstractmethod
    def start(self, *args, **kwargs):
        pass


class Progressable(abc.ABC):
    @abc.abstractmethod
    def get_progress(self) -> float:
        pass

    @abc.abstractmethod
    def set_progress(self, progress: float):
        pass

    def get_progress_label(self) -> str:
        return f"{self.get_progress():.1f}%"


class Statusable(abc.ABC):
    @abc.abstractmethod
    def get_status(self) -> StatusesEnum:
        pass

    @abc.abstractmethod
    def get_status_message(self) -> str:
        pass


class Completable(abc.ABC):
    @abc.abstractmethod
    def complete(self, *args, **kwargs):
        pass


class BaseWorkContainer(Startable, Progressable, Statusable, Completable, Nameable, abc.ABC):
    def __init__(self):
        super().__init__()


class BaseWorkContainerGroup(Progressable, Statusable, Completable, Nameable, abc.ABC):
    @abc.abstractmethod
    def get_latest_status_message(self):
        pass

    @abc.abstractmethod
    def get_status_messages(self):
        pass

    @abc.abstractmethod
    def get_num_by_status(self, status: StatusesEnum):
        pass
