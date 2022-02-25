from abc import ABC, abstractmethod
from typing import Callable, List

from base_dash_app.components.callback_utils.mappers import InputToState


class BaseComponent(ABC):
    @abstractmethod
    def render(self, *args, **kwargs):
        pass

    @staticmethod
    def get_callback_definitions() -> List[InputToState]:
        return []