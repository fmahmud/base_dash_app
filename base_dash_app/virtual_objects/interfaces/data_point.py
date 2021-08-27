from abc import ABC, abstractmethod
from typing import List


class DataPoint(ABC):
    @abstractmethod
    def contains(self, dimension: "Dimension"):
        pass

    @abstractmethod
    def contains_all(self, dimensions: List["Dimension"]):
        pass
