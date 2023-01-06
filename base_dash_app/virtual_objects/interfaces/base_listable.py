from abc import ABC, abstractmethod


class BaseListable(ABC):
    @abstractmethod
    def get_list_component(self):
        pass