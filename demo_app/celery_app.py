import time

time.sleep(10)

import logging

import dash_bootstrap_components as dbc
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


db_descriptor: DbDescriptor = DbDescriptor(
    db_uri="db:5432/testdb",
    engine_type=DbEngineTypes.POSTGRES,
    username="postgres",
    password="password",
)

my_app_descriptor = AppDescriptor(
    db_descriptor=db_descriptor,
    title="Test App",
    views=[DemoView, AreaGraphView, AsyncDemoView],
    view_groups={"Test": [DemoView]},
    jobs=[TestJobDef], service_classes=[MySelectablesService],
    use_auth=True,
    valid_user_pairs={"test": "test"},
    log_level=logging.INFO,
    alerts_refresh_timeout=2000,
    assets_folder_path="/assets",
    # std_out_formatter=ColoredFormatter()
    env_vars=[
        EnvVarDefinition(
            name="TEST_ENV_VAR", var_type=bool, required=True
        )
    ],
    use_scoped_session=True,
)

from base_dash_app.application.celery_decleration import CelerySingleton

celery = CelerySingleton.get_instance().get_celery()

rta = RuntimeApplication(my_app_descriptor)
rta.celery = celery
app = rta.app
server = rta.server
db_manager = rta.dbm