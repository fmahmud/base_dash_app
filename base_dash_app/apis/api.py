from abc import ABC
from enum import Enum
from typing import Dict, Tuple

from base_dash_app.apis.endpoint import Endpoint
from base_dash_app.enums.http_methods import HttpMethod

## TODO
class AuthTypes(Enum):
    NONE = 0
    BASIC = 1
    BEARER = 2
    DIGEST = 3
    OAUTH = 4
    QUERY_PARAM_API_KEY = 5


class API(ABC):
    def __init__(
            self, url: str, auth_type: AuthTypes, *,
            common_headers: Dict[str, str] = None,
    ):
        self.url: str = url
        self.auth_type: AuthTypes = auth_type
        self.endpoints: Dict[Tuple[str, HttpMethod], Endpoint] = {}

    def get_basic_auth(self):
        if self.auth_type == AuthTypes.BASIC:
            return

    def add_endpoint(self, path: str, http_method: HttpMethod):
        if (path, http_method) in self.endpoints:
            raise Exception("This endpoint already exists")

        self.endpoints[(path, http_method)] = Endpoint(self, path, http_method)