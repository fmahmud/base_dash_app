from abc import ABC, ABCMeta
from typing import TypeVar, Type, List, Generic

from sqlalchemy.orm import Session

from base_dash_app.models.base_model import BaseModel
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject

T = TypeVar("T", bound=BaseModel)  # Declare type variable


class AbstractSingleton(ABCMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


class BaseService(ABC, Generic[T], VirtualFrameworkObject, metaclass=AbstractSingleton):

    def __init__(self, service_name: str = None, object_type: Type[T] = None, **kwargs):
        super().__init__(**kwargs)
        self.__service_name = service_name if service_name is not None else self.__class__.__name__
        self.object_type = object_type

    def get_by_id(self, id: int, session: Session) -> T:
        if session is None:
            raise Exception("No Session provided.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        return session.query(self.object_type).get(id)

    def get_all(self, session: Session) -> List[T]:
        if session is None:
            raise Exception("No Session provided.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        return session.query(self.object_type).all()

    def save(self, target: T, session: Session) -> T:
        if session is None:
            raise Exception("No Session provided.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        try:
            session.add(target)
            session.expire_on_commit = False
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

        return target

    def save_all(self, targets: List[T], session: Session) -> List[T]:
        if session is None:
            raise Exception("No Session provided.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        try:
            session.add_all(targets)
            session.expire_on_commit = False
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

        return targets
