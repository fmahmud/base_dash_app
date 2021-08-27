import logging
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from typing import TypeVar, Type, List, Generic, Callable, Union

from base_dash_app.models.base_model import BaseModel
from base_dash_app.utils.db_utils import DbManager

T = TypeVar("T", bound=BaseModel)  # Declare type variable


class BaseService(ABC, Generic[T]):
    def __init__(self, dbm: DbManager, service_name: str, object_type: Type[T], service_provider: Callable = None):
        self.dbm: DbManager = dbm
        self.logger = logging.getLogger(service_name)
        self.object_type = object_type
        self.get_service = service_provider

    def get_by_id(self, id: int) -> T:
        session: Session = self.dbm.get_session()
        return session.query(self.object_type).filter_by(id=id).first()

    def get_all(self) -> List[T]:
        session: Session = self.dbm.get_session()
        return session.query(self.object_type).all()

    @abstractmethod
    def get_n_sized_combination(self, n: int, values: List[T]) -> List[List[T]]:
        pass

    def save(self, target: T) -> T:
        session: Session = self.dbm.get_session()
        session.add(target)
        session.commit()

        # todo: check if this is augmented or not
        return target

    def save_all(self, targets: List[T]) -> List[T]:
        session: Session = self.dbm.get_session()
        session.add_all(targets)
        session.commit()

        # todo: check if this is augmented or not
        return targets
