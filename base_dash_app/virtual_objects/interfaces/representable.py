from abc import ABC, abstractmethod
from typing import FrozenSet, Tuple, Union


class Representable(ABC):
    @abstractmethod
    def get_repr(self) -> Union[Tuple, FrozenSet]:
        pass

    def __hash__(self):
        return self.get_repr()


class RepresentableInGT(Representable, ABC):
    @staticmethod
    @abstractmethod
    def get_dim_repr_from_game_team(game_team):
        pass

    @staticmethod
    @abstractmethod
    def get_repr_for_class(dim):
        pass
