import datetime

from base_dash_app.apis.handlers.token_handlers.token_handler import TokenHandler
from base_dash_app.apis.utils import api_utils
from base_dash_app.apis.utils.request import Request
from base_dash_app.enums.http_methods import HttpMethods
from base_dash_app.models.oauth_provider import OAuthProvider
from base_dash_app.models.token import Token


class PlaintextOAuthHandler(TokenHandler):
    def __init__(self, oauth_provider: OAuthProvider):
        super().__init__(oauth_provider)

    '''{"email": "---@---.com","password":{"plaintext":"---"}}'''

    def populate_token_with_response_data(self, response, token: Token, now: datetime.datetime):
        '''{
            "data": [
                {
                    "accessToken": "",
                    "tokenType": "Bearer",
                    "expiresIn": 43200
                }
            ],
            "warnings": null,
            "errors": null,
            "request": {
                "id": "c07a2e62-8571-11eb-913f-aae34a2da4cd",
                "timestamp": "2021-03-15T09:35:17.778Z"
            }
        }'''
        if "data" in response:
            if len(response["data"]) > 0:
                # first token only
                token_data = response["data"][0]
                if "accessToken" in token_data:
                    token.access_token = token_data["accessToken"]

                if "expiresIn" in token_data:
                    token.valid_until = now + datetime.timedelta(seconds=token_data["expiresIn"])

    def build_oauth_request(self, client_id, client_secret):
        request = Request(
            method=HttpMethods.POST.value,
            url=self.oauth_provider.token_endpoint,
            url_params={},
            body={
                "email": client_id,
                "password": {
                    "plaintext": client_secret
                },
            },
            headers=api_utils.get_base_header()
        )

        return request