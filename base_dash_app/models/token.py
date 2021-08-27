import datetime

from sqlalchemy import Column, Integer, String, DateTime, Sequence, ForeignKey

from base_dash_app.models.base_model import BaseModel


class Token(BaseModel):
    __tablename__ = "tokens"

    id = Column(Integer, Sequence("token_id_seq"), primary_key=True)

    client_id = Column(Integer, ForeignKey("clients.id"))
    date_created = Column(DateTime)
    valid_until = Column(DateTime)
    access_token = Column(String)
    scope = Column(String)

    def __lt__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "date_created": self.date_created,
            "valid_until": self.valid_until,
            "access_token": self.access_token,
            "scope": self.scope,
        }

    def __str__(self):
        return str(self.to_dict())

    def is_active(self) -> bool:
        return datetime.datetime.utcnow() < self.valid_until
