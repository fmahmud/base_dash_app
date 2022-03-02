from abc import ABC, abstractmethod
from typing import Callable


class Selectable(ABC):
    @abstractmethod
    def get_label(self):
        pass

    @abstractmethod
    def get_value(self):
        pass

