from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import relationship

from base_dash_app.models.base_model import BaseModel


class Dashboard(BaseModel):
    __tablename__ = "dashboards"

    id = Column(Integer, Sequence("dashboard_id_seq"), primary_key=True)

    name = Column(String)
    title = Column(String)

    author = Column(String)
    description = Column(String)
    test_groups = relationship("TestGroup")

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