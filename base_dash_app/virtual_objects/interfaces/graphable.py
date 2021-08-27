from abc import ABC, abstractmethod


class Graphable(ABC):
    @abstractmethod
    def get_x(self):
        pass

    @abstractmethod
    def get_y(self):
        pass

    @abstractmethod
    def get_label(self):
        pass