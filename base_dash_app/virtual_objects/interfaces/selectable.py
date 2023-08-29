from abc import ABC, abstractmethod
from typing import List

from dash import html


class Selectable(ABC):
    def get_label_div(self):
        return html.H4(self.get_label())

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

    def __str__(self):
        return f"{self.get_label()}:{self.get_value()}"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return hash(self) == hash(other)


class CachedSelectable(Selectable):
    @staticmethod
    def from_selectable(selectable: Selectable) -> 'CachedSelectable':
        return CachedSelectable(
            label=selectable.get_label(),
            value=selectable.get_value(),
            label_div=selectable.get_label_div()
        )

    def __init__(self, label, value, label_div=None):
        self.label = label
        self.value = value
        self.label_div = label_div or super().get_label_div()

    def get_label_div(self):
        return self.label_div

    def get_label(self):
        return self.label

    def get_value(self):
        return self.value
