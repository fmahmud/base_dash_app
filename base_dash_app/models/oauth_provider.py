from sqlalchemy import Column, Integer, String, Sequence

from base_dash_app.models.base_model import BaseModel


class OAuthProvider(BaseModel):
    __tablename__ = "oauth_providers"

    id = Column(Integer, Sequence("oauth_provider_id_seq"), primary_key=True)

    name = Column(String)
    token_endpoint = Column(String)
    authorization_type = Column(Integer)

    def __lt__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def to_dict(self):
        pass