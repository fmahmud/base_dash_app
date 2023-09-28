from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Tuple, Callable, Any, List, Union

from base_dash_app.apis.endpoint import Endpoint
from base_dash_app.apis.utils import api_utils
from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethod
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject


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


class NoAuthHandler(AuthHandler):
    def add_auth_to_request(self, request: Request):
        pass


#issue: (issue: 174): Allow setting communication type: json (def), xml, etc.
class API(VirtualFrameworkObject, ABC):
    def __init__(
            self, url: str, auth_handler: AuthHandler = None, *,
            common_headers: Dict[str, str] = None,
            **kwargs
    ):
        VirtualFrameworkObject.__init__(self, **kwargs)
        self.url: str = url
        self.auth_handler: AuthHandler = auth_handler if auth_handler is not None else NoAuthHandler()
        self.__endpoints: Dict[Tuple[str, HttpMethod], Endpoint] = {}
        self.common_headers: Dict[str, str] = common_headers if common_headers is not None else {}
        self.functions: Dict[str, Callable] = {}

    def add_endpoint(self, path: str, http_method: HttpMethod, name: str):

        if (path, http_method) in self.__endpoints:
            raise ValueError("This endpoint already exists")

        endpoint: Endpoint = Endpoint(self, path, http_method)
        self.__endpoints[(path, http_method)] = endpoint

        def make_request(
                path_params: Dict[str, str],
                *,
                body: str = None,
                additional_headers: Dict[str, str] = None,
                query_params: Dict[str, Any] = None,
                timeout: int = 200
        ) -> Tuple[Union[Dict, List], int]:
            return api_utils.make_request(
                endpoint.get_as_request(
                    path_params=path_params,
                    body=body,
                    additional_headers=additional_headers,
                    query_params=query_params,
                    timeout=timeout
                )
            )

        self.functions[name] = make_request
        return make_request

    @staticmethod
    def endpoint_def(path: str, http_method: HttpMethod, timeout: int = 200, parse_json: bool = True):

        def inner_func(result_handler: Callable[[Union[Dict, List], int], Any]):

            def wrapper(*args, **kwargs):
                if "path_params" in kwargs:
                    path_params = kwargs["path_params"]
                else:
                    path_params = {}

                if "body" in kwargs:
                    body = kwargs["body"]
                else:
                    body = None

                if "additional_headers" in kwargs:
                    additional_headers = kwargs["additional_headers"]
                else:
                    additional_headers = None

                if "query_params" in kwargs:
                    query_params = kwargs["query_params"]
                else:
                    query_params = None

                # args[0] should be the API instance the endpoint is being defined in
                ep_to_call: Endpoint = Endpoint(args[0], path, http_method)
                response, status = api_utils.make_request(
                    ep_to_call.get_as_request(
                        path_params=path_params,
                        body=body,
                        additional_headers=additional_headers,
                        query_params=query_params,
                        timeout=timeout
                    ),
                    parse_json=parse_json
                )

                return result_handler(response, status)

            return wrapper

        return inner_func
