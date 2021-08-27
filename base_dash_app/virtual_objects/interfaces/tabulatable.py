import abc
from typing import Dict, List


class Tabulatable(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_columns() -> List[Dict[str, str]]:
        pass

    @abc.abstractmethod
    def to_table_data(self):
        pass