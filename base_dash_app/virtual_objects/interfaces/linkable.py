from abc import ABC, abstractmethod
from typing import Set

all_links: Set[str] = set()


class Linkable(ABC):
    # def __init__(self):
        # all_links.add(self.get_link())


    @abstractmethod
    def get_link(self) -> str:
        pass
