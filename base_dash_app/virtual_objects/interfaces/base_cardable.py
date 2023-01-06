import abc
from abc import ABC


class BaseCardable(ABC):
    @abc.abstractmethod
    def get_card_component(self):
        pass