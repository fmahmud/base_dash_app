from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Tuple, Callable, Any

from base_dash_app.apis.endpoint import Endpoint
from base_dash_app.apis.utils import api_utils
from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethod


# TODO
class AuthTypes(Enum):
    NONE = 0
    BASIC = 1
    BEARER = 2
    DIGEST = 3
    OAUTH = 4
    QUERY_PARAM_API_KEY = 5


class AuthHandler(ABC):
    @abstractmethod
    def add_auth_to_request(self, request: Request):
        pass


class BasicAuthHandler(AuthHandler):
    def __init__(self, username: str, password: str):
        self.username: str = username
        self.password: str = password

    def add_auth_to_request(self, request: Request):
        request.auth = (self.username, self.password)


class API(ABC):
    def __init__(
            self, url: str, auth_handler: AuthHandler, *,
            common_headers: Dict[str, str] = None
    ):
        self.url: str = url
        self.auth_handler: AuthHandler = auth_handler
        self.__endpoints: Dict[Tuple[str, HttpMethod], Endpoint] = {}
        self.common_headers: Dict[str, str] = common_headers if common_headers is not None else {}
        self.functions: Dict[str, Callable] = {}

    def add_endpoint(self, path: str, http_method: HttpMethod, name: str):
        if (path, http_method) in self.__endpoints:
            raise Exception("This endpoint already exists")

        endpoint: Endpoint = Endpoint(self, path, http_method)
        self.__endpoints[(path, http_method)] = endpoint

        def make_request(
            path_params: Dict[str, str],
            *,
            body: str = None,
            additional_headers: Dict[str, str] = None,
            query_params: Dict[str, Any] = None
        ):
            return api_utils.make_request(
                endpoint.get_as_request(
                    path_params=path_params,
                    body=body,
                    additional_headers=additional_headers,
                    query_params=query_params
                )
            )

        self.functions[name] = make_request
