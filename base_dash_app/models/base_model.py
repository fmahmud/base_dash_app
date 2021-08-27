import abc
from abc import ABC, abstractmethod

from sqlalchemy.ext.declarative import DeclarativeMeta

from base_dash_app.utils.base_definition import get_base_class


class DeclarativeABCMeta(DeclarativeMeta, abc.ABCMeta):
    pass


class BaseModel(get_base_class(), ABC, metaclass=DeclarativeABCMeta):
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

    @abstractmethod
    def to_dict(self):
        pass
