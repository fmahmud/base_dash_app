from sqlalchemy import Column, Integer, String, Sequence, ForeignKey

from base_dash_app.models.base_model import BaseModel


class Client(BaseModel):
    __tablename__ = "clients"

    id = Column(Integer, Sequence("client_id_seq"), primary_key=True)

    name = Column(String)
    client_id = Column(String)

    client_secret = Column(String)
    oauth_provider_id = Column(Integer, ForeignKey("oauth_providers.id"))

    def __lt__(self, other):
        if type(other) != Client:
            raise Exception("Other is of type %s, should be Client." % type(other))
        return self.id < other.id

    def __eq__(self, other):
        if type(other) != Client:
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "client_id": self.client_id,
            "oauth_provider_id": self.oauth_provider_id
        }
