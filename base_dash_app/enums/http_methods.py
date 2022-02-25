from enum import unique, Enum
from typing import Callable

import requests


class HttpMethod:
    def __init__(self, id, name, function: Callable):
        self.id = id
        self.name = name
        self.function = function

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

    def __hash__(self):
        return hash(self.name)


@unique
class HttpMethods(Enum):
    GET = HttpMethod(1, "GET", requests.get)
    POST = HttpMethod(2, "POST", requests.post)
    PUT = HttpMethod(3, "PUT", requests.put)
    DELETE = HttpMethod(4, "DELETE", requests.delete)
    OPTIONS = HttpMethod(5, "OPTIONS", requests.options)

    def __str__(self):
        return self.value

    @staticmethod
    def get_by_id(id: int) -> "HttpMethods":
        for e in HttpMethods:
            if e.value.id == id:
                return e

        raise Exception("No HttpMethod with id = " + str(id))
