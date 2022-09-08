from abc import ABC
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from base_dash_app.apis.api import API

from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethod
from base_dash_app.utils import utils


class Endpoint:
    def __init__(self, api: 'API', path: str, http_method: HttpMethod):
        self.api: 'API' = api
        self.path: str = path
        self.http_method: HttpMethod = http_method

    def get_as_request(
            self, path_params: Dict[str, str],
            *,
            body: str = None,
            additional_headers: Dict[str, str] = None,
            query_params: Dict[str, Any] = None,
            timeout: int = 200
    ):
        additional_headers = {} if additional_headers is None else additional_headers

        constructed_path: str = self.path
        for k, v in path_params.items():
            constructed_path = constructed_path.replace(k, str(v))

        request: Request = Request(
            method=self.http_method,
            url=self.api.url + constructed_path,
            query_params=query_params,
            body=body,
            headers=utils.apply(self.api.common_headers, additional_headers),
            timeout=timeout
        )

        self.api.auth_handler.add_auth_to_request(request)

        return request
