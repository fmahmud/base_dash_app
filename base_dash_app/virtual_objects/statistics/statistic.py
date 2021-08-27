from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base_dash_app.virtual_objects.interfaces.resultable import Resultable


class Statistic(ABC):
    def __init__(self, *, starting_value: float = 0.0):
        self.value: float = starting_value

    @abstractmethod
    def process_result(self, result: float):
        pass

    def process_resultable(self, resultable: "Resultable"):
        return self.process_result(resultable.get_result())

    def get_statistic(self):
        return self.value
