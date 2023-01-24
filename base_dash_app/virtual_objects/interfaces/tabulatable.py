import abc
from typing import Dict, List, Any


class Tabulatable(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_column_definitions() -> List[Dict[str, str]]:
        pass

    @abc.abstractmethod
    def to_row_data(self) -> Dict[str, Any]:
        pass

