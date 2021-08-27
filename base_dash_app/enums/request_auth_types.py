from enum import Enum
from typing import Callable, Tuple, Optional, Dict, Any


class RequestAuthType:
    # should this return dictionaries instead?
    def __init__(self, id: int, name: str, header_provider: Callable[[str], Optional[Dict[str, str]]]):
        self.id = id
        self.name = name
        self.get_header_for_token = header_provider


class RequestAuthTypes(Enum):
    BearerToken = RequestAuthType(1, "Bearer Token", lambda token: {"Authorization": "Bearer " + token})
    NoAuth = RequestAuthType(2, "No Authorization", lambda: None)

    @staticmethod
    def get_by_id(id: int) -> "RequestAuthTypes":
        for e in RequestAuthTypes:
            if e.value.id == id:
                return e

        raise Exception("No RequestAuthType with id = " + str(id))
