from abc import ABC, abstractmethod
from typing import Type

from base_dash_app.models.base_model import DimensionModel
from base_dash_app.virtual_objects.interfaces.linkable import Linkable
from base_dash_app.virtual_objects.interfaces.nameable import Nameable
from base_dash_app.virtual_objects.interfaces.representable import Representable


class Dimension(Representable, Nameable, Linkable, ABC):
    def __init__(self, base_item: DimensionModel):
        super().__init__()
        self.base_item: DimensionModel = base_item

    @staticmethod
    @abstractmethod
    def elements_are_unique():
        pass

    @staticmethod
    @abstractmethod
    def get_dimension_name() -> str:
        pass

    def get_name(self):
        return self.base_item.get_name()

    def get_color(self):
        return self.base_item.get_color()

    @staticmethod
    @abstractmethod
    def get_base_class() -> Type[DimensionModel]:
        pass

    @abstractmethod
    def __lt__(self, other):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass