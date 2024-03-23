import abc
from abc import abstractmethod

from flask_sqlalchemy import DefaultMeta

from base_dash_app.application.db_declaration import db


class CombinedMeta(abc.ABCMeta, DefaultMeta):
    pass


class BaseModel(db.Model, metaclass=CombinedMeta):
    __abstract__ = True

    @abstractmethod
    def __lt__(self, other):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def to_dict(self):
        return vars(self)

