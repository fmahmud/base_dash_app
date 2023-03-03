from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from base_dash_app.virtual_objects.interfaces.dimension import Dimension


class DataPoint(ABC):
    @abstractmethod
    def contains(self, dimension: "Dimension"):
        pass

    @abstractmethod
    def contains_all(self, dimensions: List["Dimension"]):
        pass
