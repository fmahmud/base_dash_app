from base_dash_app.apis.handlers.token_handlers.oauth_token_handler import OAuthTokenHandler
from base_dash_app.apis.handlers.token_handlers.plaintext_oauth import PlaintextOAuthHandler
from base_dash_app.apis.handlers.token_handlers.token_handler import TokenHandler
from base_dash_app.models.oauth_provider import OAuthProvider


def get_token_for_oauth_provider(oauth_provider: OAuthProvider) -> TokenHandler:
    if oauth_provider.authorization_type == 1:
        return OAuthTokenHandler(oauth_provider)
    elif oauth_provider.authorization_type == 2:
        return PlaintextOAuthHandler(oauth_provider)

    raise Exception("Unexpected authorization type %i" % oauth_provider.authorization_type)