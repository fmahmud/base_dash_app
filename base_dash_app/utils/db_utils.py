from enum import Enum

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from base_dash_app.utils.base_definition import get_base_class


class DbEngineTypes(Enum):
    POSTGRES = 'postgresql://'
    POSTGRES_PSYCO = 'postgresql+psycopg://'
    SQLITE = 'sqlite:///'


class DbDescriptor:
    def __init__(
            self,
            db_uri: str, engine_type: DbEngineTypes = DbEngineTypes.SQLITE,
            username: str = None, password: str = None,
            check_same_thread: bool = False,
            echo: bool = False,
            schema: str = None
    ):
        self.db_uri: str = db_uri
        self.engine_type: DbEngineTypes = engine_type
        self.username: str = username
        self.password: str = password
        self.check_same_thread: bool = check_same_thread
        self.echo: bool = echo
        self.schema: str = schema


class DbManager:
    def __init__(self, db_descriptor: DbDescriptor):
        self.db_descriptor: DbDescriptor = db_descriptor

        check_thread_string = ""
        if self.db_descriptor.engine_type == DbEngineTypes.SQLITE:
            auth_str = ""
            check_thread_string = f"?check_same_thread={self.db_descriptor.check_same_thread}"
        else:
            auth_str = (self.db_descriptor.username + ':' + self.db_descriptor.password + "@") \
                if None not in [self.db_descriptor.username, self.db_descriptor.password] else ""

        self.__db_con_string = f"{self.db_descriptor.engine_type.value}" \
                               f"{auth_str}" \
                               f"{self.db_descriptor.db_uri}" \
                               f"{check_thread_string}"

        self.connection_args = {}
        if db_descriptor.schema is not None:
            self.connection_args = {
                'options': '-csearch_path={}'.format(db_descriptor.schema)
            }

        self.__engine = create_engine(
            self.__db_con_string, echo=self.db_descriptor.echo,
            connect_args=self.connection_args
        )
        self.__connection = self.__engine.connect()
        self.__Session = sessionmaker(bind=self.__engine)
        self.session = self.__Session()

    def upgrade_db(self):
        get_base_class().metadata.create_all(self.__engine)

    def get_session(self) -> Session:
        return self.session

    def new_session(self):
        return self.__Session()

