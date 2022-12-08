from abc import ABC, abstractmethod
from typing import List


class Selectable(ABC):
    @abstractmethod
    def get_label(self):
        pass

    @abstractmethod
    def get_value(self):
        pass

    @classmethod
    def get_label_type(cls):
        pass

    @classmethod
    def get_value_type(cls):
        pass


class CachedSelectable(Selectable):
    @staticmethod
    def from_selectable(selectable: Selectable) -> 'CachedSelectable':
        return CachedSelectable(selectable.get_label(), selectable.get_value())

    def __init__(self, label, value):
        self.label = label
        self.value = value

    def get_label(self):
        return self.label

    def get_value(self):
        return self.value
