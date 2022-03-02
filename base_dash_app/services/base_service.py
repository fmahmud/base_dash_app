import logging
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from typing import TypeVar, Type, List, Generic, Callable, Union, Optional

from base_dash_app.models.base_model import BaseModel
from base_dash_app.utils.db_utils import DbManager

T = TypeVar("T", bound=BaseModel)  # Declare type variable


class BaseService(ABC, Generic[T]):
    def __init__(self, dbm: Optional[DbManager], service_name: str, object_type: Type[T] = None, service_provider: Callable = None):
        self.dbm: Optional[DbManager] = dbm
        self.logger = logging.getLogger(service_name)
        self.object_type = object_type
        self.get_service = service_provider
        self.__service_name = service_name

    def get_by_id(self, id: int) -> T:
        if self.dbm is None:
            raise Exception("No DB configured.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        session: Session = self.dbm.get_session()
        return session.query(self.object_type).filter_by(id=id).first()

    def get_all(self) -> List[T]:
        if self.dbm is None:
            raise Exception("No DB configured.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        session: Session = self.dbm.get_session()
        return session.query(self.object_type).all()

    def save(self, target: T) -> T:
        if self.dbm is None:
            raise Exception("No DB configured.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        session: Session = self.dbm.get_session()
        session.add(target)
        session.commit()

        return target

    def save_all(self, targets: List[T]) -> List[T]:
        if self.dbm is None:
            raise Exception("No DB configured.")

        if self.object_type is None:
            raise Exception(f"Service {self.__service_name} is not a model providing service.")

        session: Session = self.dbm.get_session()
        session.add_all(targets)
        session.commit()

        return targets
