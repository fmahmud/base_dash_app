from abc import ABC, abstractmethod


class Searchable(ABC):

    @abstractmethod
    def compare_with_search_string(self, search_string) -> bool:
        pass
