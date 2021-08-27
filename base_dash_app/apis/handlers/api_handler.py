import logging
from abc import ABC, abstractmethod

from base_dash_app.apis.utils import api_utils
from base_dash_app.apis.utils.request import Request
from base_dash_app.apis.handlers.token_handlers.token_handler import TokenHandler
from base_dash_app.models.client import Client
from base_dash_app.models.token import Token


class ApiHandler(ABC):
    def __init__(self, token_manager: TokenHandler, logger: logging.Logger):
        self.token_manager = token_manager
        self.logger: logging.Logger = logger

    @abstractmethod
    def add_authorization_to_request(self, request: Request, token: Token):
        pass

    def make_authorized_request(self, request: Request, client: Client):
        token: Token = self.token_manager.get_token_for_client(client)
        self.add_authorization_to_request(request, token)
        return api_utils.make_request(request)
