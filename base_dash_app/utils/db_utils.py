from enum import Enum
from threading import local

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

from base_dash_app.application.db_declaration import db


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
            timeout: int = 15,
            use_pool: bool = False,
            pool_size: int = 10,
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
        self.use_pool: bool = use_pool
        self.pool_size: int = pool_size


class DbManager:
    _thread_local_data = local()

    # def __new__(cls, db_descriptor: DbDescriptor, app: Flask, db: SQLAlchemy):
    #     if cls._instance is None:
    #         cls._instance = super(DbManager, cls).__new__(cls)
    #         cls._instance.__init__(db_descriptor, app, db)
    #     return cls._instance

    def __init__(self, db_descriptor: DbDescriptor, app: Flask):
        self.db_descriptor: DbDescriptor = db_descriptor
        self.connection_args = {}

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

        if db_descriptor.schema is not None and 'options' not in self.connection_args:
            self.connection_args = {
                'options': '-csearch_path={}'.format(db_descriptor.schema)
            }

        # Flask-SQLAlchemy specific configuration
        app.config['SQLALCHEMY_DATABASE_URI'] = self.__db_con_string
        app.config['SQLALCHEMY_ECHO'] = self.db_descriptor.echo
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': self.connection_args
        }
        app.config['SQLALCHEMY_POOL_SIZE'] = self.db_descriptor.pool_size

        self.db: SQLAlchemy = db
        if "sqlalchemy" not in app.extensions:
            self.db.init_app(app)
        self.app = app

        if self.db_descriptor.engine_type == DbEngineTypes.SQLITE:
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

            event.listen(self.db.engine, 'connect', set_sqlite_pragma)

        @self.app.before_request
        def before_request():
            self.__enter__()

        @self.app.teardown_request
        def teardown_request(exception: Exception = None):
            if exception is None:
                self.__exit__(None, None, None)
            else:
                self.__exit__(exception.__class__, exception, exception.__traceback__)

        @self.app.teardown_appcontext
        def shutdown_session(exception=None):
            self.db.session.remove()

    def upgrade_db(self, drop_first: bool = False):
        if drop_first:
            self.db.drop_all()

        self.db.create_all()

    def get_session(self):
        return self.db.session

    def new_session(self):
        return self.db.create_scoped_session()

    def __enter__(self):
        # Create a new app context for this thread if it doesn't exist yet.
        if not hasattr(self._thread_local_data, 'app_context'):
            self._thread_local_data.app_context = self.app.app_context()
        self._thread_local_data.app_context.push()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only pop the context if it exists for this thread.
        if hasattr(self._thread_local_data, 'app_context'):
            self._thread_local_data.app_context.pop()
