import datetime
import logging
from abc import abstractmethod, ABC

from base_dash_app.apis.utils import api_utils
from base_dash_app.models.client import Client
from base_dash_app.models.oauth_provider import OAuthProvider
from base_dash_app.models.token import Token


class TokenHandler(ABC):
    def __init__(self, oauth_provider: OAuthProvider):
        self.oauth_provider: OAuthProvider = oauth_provider
        self.logger = logging.getLogger(name="TokenHandler(" + str(oauth_provider.id) + ")")

    @abstractmethod
    def build_oauth_request(self, client_id, client_secret):
        pass

    def __get_oauth_token_with_credentials(self, client_id, client_secret):
        oauth_request = self.build_oauth_request(client_id, client_secret)

        self.logger.info("request = %s", oauth_request)

        response_as_json, status_code = api_utils.make_request(oauth_request)

        if status_code == 200:
            return response_as_json
        else:
            raise Exception('Unknown error occurred.', response_as_json)

    @abstractmethod
    def populate_token_with_response_data(self, response, token: Token, now: datetime.datetime):
        pass

    def __get_new_token_for_client(self, client: Client) -> Token:

        now = datetime.datetime.utcnow()
        self.logger.debug("Need to get new token for client %s", client.client_id)

        token_response = self.__get_oauth_token_with_credentials(client.client_id, client.client_secret)
        token = Token()
        token.client_id = client.id
        token.date_created = now

        self.populate_token_with_response_data(token_response, token, now)

        return token

    def get_token_for_client(self, client: Client) -> Token:
        return self.__get_new_token_for_client(client)
