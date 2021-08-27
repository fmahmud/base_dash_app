import datetime

from base_dash_app.apis.handlers.token_handlers.token_handler import TokenHandler
from base_dash_app.apis.utils import api_utils
from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethods
from base_dash_app.models.oauth_provider import OAuthProvider
from base_dash_app.models.token import Token


class OAuthTokenHandler(TokenHandler):
    def populate_token_with_response_data(self, response, token: Token, now: datetime.datetime):
        if 'access_token' in response:
            # todo: raise exception if no access_token?
            token.access_token = response["access_token"]

        if "expires_in" in response:
            # todo: raise exception if no expires_in?
            token.valid_until = now + datetime.timedelta(seconds=response["expires_in"])

        if "scope" in response:
            token.scope = response["scope"]

    def __init__(self, oauth_provider: OAuthProvider):
        super().__init__(oauth_provider)

    def build_oauth_request(self, client_id, client_secret):
        request = Request(
            method=HttpMethods.POST.value,
            url=self.oauth_provider.token_endpoint,
            url_params={},
            body={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            },
            headers=api_utils.get_base_header()
        )

        return request
