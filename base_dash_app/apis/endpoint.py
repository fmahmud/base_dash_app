from abc import ABC
from typing import Dict, Any

from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethod
from base_dash_app.utils import utils


class Endpoint(ABC):
    def __init__(self, api, path: str, http_method: HttpMethod):
        self.api = api
        self.path: str = path
        self.http_method: HttpMethod = http_method

    def get_as_request(
            self, path_params: Dict[str, str],
            *,
            body: str = None,
            additional_headers: Dict[str, str] = None,
            query_params: Dict[str, Any] = None
    ):

        constructed_path: str = self.path
        for k, v in path_params.items():
            constructed_path.replace(k, v)

        request: Request = Request(
            method=self.http_method,
            url=self.api.get_url() + constructed_path,
            query_params=query_params,
            body=body,
            headers=utils.apply_all_to_dict({}, **self.api.get_headers(), **additional_headers),
            auth=self.api.get_basic_auth()
        )

        return request
