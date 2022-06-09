from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from base_dash_app.utils.base_definition import get_base_class


class DbManager:
    def __init__(self, db_file: str):
        self.__db_file = "sqlite:///%s?check_same_thread=False" % db_file
        self.__engine = create_engine(self.__db_file, echo=False)
        self.__connection = self.__engine.connect()
        self.__Session = sessionmaker(bind=self.__engine)
        self.session = self.__Session()

    def upgrade_db(self):
        get_base_class().metadata.create_all(self.__engine)

    def get_session(self) -> Session:
        return self.session

    def new_session(self):
        return self.__Session()
