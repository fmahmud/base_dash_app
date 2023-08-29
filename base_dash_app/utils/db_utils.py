from enum import Enum

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session

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
            schema: str = None,
            use_wal: bool = False,
            timeout: int = 15
    ):
        self.db_uri: str = db_uri
        self.engine_type: DbEngineTypes = engine_type
        self.username: str = username
        self.password: str = password
        self.check_same_thread: bool = check_same_thread
        self.echo: bool = echo
        self.schema: str = schema
        self.use_wal: bool = use_wal or self.engine_type == DbEngineTypes.SQLITE
        self.timeout: int = timeout


class DbManager:
    def __init__(self, db_descriptor: DbDescriptor, use_scoped_sessions: bool = False):
        self.db_descriptor: DbDescriptor = db_descriptor
        self.use_scoped_sessions = use_scoped_sessions
        self.connection_args = {}

        check_thread_string = ""
        if self.db_descriptor.engine_type == DbEngineTypes.SQLITE:
            self.connection_args['check_same_thread'] = self.db_descriptor.check_same_thread
            self.connection_args['timeout'] = self.db_descriptor.timeout
            auth_str = ""
        else:
            auth_str = (self.db_descriptor.username + ':' + self.db_descriptor.password + "@") \
                if None not in [self.db_descriptor.username, self.db_descriptor.password] else ""

        self.__db_con_string = f"{self.db_descriptor.engine_type.value}" \
                               f"{auth_str}" \
                               f"{self.db_descriptor.db_uri}"
                               # f"{check_thread_string}"

        if db_descriptor.schema is not None:
            self.connection_args = {
                'options': '-csearch_path={}'.format(db_descriptor.schema)
            }

        self.__engine = create_engine(
            self.__db_con_string, echo=self.db_descriptor.echo,
            connect_args=self.connection_args
        )

        if self.db_descriptor.engine_type == DbEngineTypes.SQLITE:
            @event.listens_for(self.__engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

        self.__connection = self.__engine.connect()
        self.__Session = sessionmaker(bind=self.__engine, expire_on_commit=False)
        if self.use_scoped_sessions:
            self.__Session = scoped_session(self.__Session)

        self.session = self.new_session()

    def upgrade_db(self, drop_first: bool = False):
        if drop_first:
            get_base_class().metadata.drop_all(self.__engine, checkfirst=True)

        get_base_class().metadata.create_all(self.__engine)

    def get_session(self) -> Session:
        return self.session

    def new_session(self):
        return self.__Session()

