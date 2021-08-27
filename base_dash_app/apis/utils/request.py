from typing import Dict, Tuple

from base_dash_app.enums.http_methods import HttpMethod
from base_dash_app.utils.utils import apply


class Request:
    def __init__(self, method: HttpMethod, url, url_params=None, body=None, headers=None, auth=()):
        self.method: HttpMethod = method
        self.url: str = url
        self.url_params: Dict[str, str] = url_params
        self.body = body
        self.headers: Dict[str, str] = headers
        self.auth: Tuple[str, str] = auth

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict:
        return {
            "method": self.method.to_dict(),
            "url": self.url,
            "url_params": self.url_params,
            "body": self.body,
            "headers": self.headers,
            "auth": self.auth,
        }

    def add_headers(self, headers: Dict[str, str]):
        if self.headers is None:
            self.headers = {}

        self.headers = apply(self.headers, headers)

    def add_url_params(self, params: Dict[str, str]):
        if self.url_params is None:
            self.url_params = {}

        self.url_params = apply(self.url_params, params)

    def set_auth(self, username, password):
        if self.auth is None:
            self.auth = ()

        self.auth = (username, password)


