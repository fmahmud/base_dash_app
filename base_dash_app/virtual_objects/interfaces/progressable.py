from abc import ABC, abstractmethod


class Progressable(ABC):
    @abstractmethod
    def get_progress(self):
        pass