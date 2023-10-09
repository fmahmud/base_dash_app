import logging
import os

import dash_bootstrap_components as dbc
from celery import Celery
from dash_bootstrap_components.icons import FONT_AWESOME
from dotenv import load_dotenv


load_dotenv()

from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.utils.db_utils import DbDescriptor, DbEngineTypes
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
from base_dash_app.utils.log_formatters.colored_formatter import ColoredFormatter
from demo_app.async_demo_view import AsyncDemoView
from demo_app.demo_view import DemoView, TestJobDef, MySelectablesService
from demo_app.area_graph_view import AreaGraphView

external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto&display=swap",
    dbc.themes.BOOTSTRAP,
    FONT_AWESOME
]


db_descriptor: DbDescriptor = DbDescriptor(
    db_uri="db:5432/testdb",
    engine_type=DbEngineTypes.POSTGRES,
    username="postgres",
    password="password",
)

my_app_descriptor = AppDescriptor(
    db_descriptor=db_descriptor,
    title="Test App",
    external_stylesheets=external_stylesheets,
    views=[DemoView, AreaGraphView, AsyncDemoView], view_groups={"Test": [DemoView]},
    jobs=[TestJobDef], service_classes=[MySelectablesService],
    upgrade_db=True,
    drop_tables=False,
    use_auth=True,
    valid_user_pairs={"test": "test"},
    log_level=logging.INFO,
    alerts_refresh_timeout=2000,
    assets_folder_path="/assets",
    std_out_formatter=ColoredFormatter(),
    env_vars=[
        EnvVarDefinition(
            name="TEST_ENV_VAR", var_type=bool, required=True
        )
    ],
    use_scoped_session=True,
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db_number=int(os.getenv("REDIS_DB_NUMBER", "0")),
    redis_use_ssl=os.getenv("REDIS_USE_SSL", "False").lower() == "true",
    redis_password=os.getenv("REDIS_PASSWORD", None),
)


from base_dash_app.application.celery_decleration import CelerySingleton
celery_singleton: CelerySingleton = CelerySingleton.get_instance()
celery = celery_singleton.get_celery()

rta = RuntimeApplication(my_app_descriptor)
app = rta.app
server = rta.server
server.config["TESTING"] = True

