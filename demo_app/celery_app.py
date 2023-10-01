import os
import time

time.sleep(10)

import logging

from dotenv import load_dotenv


load_dotenv()

from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.utils.db_utils import DbDescriptor, DbEngineTypes
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
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
    redis_host=os.getenv("REDIS_HOST", "redis"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db_number=int(os.getenv("REDIS_DB_NUMBER", "0")),
    redis_use_ssl=os.getenv("REDIS_USE_SSL", "False").lower() == "true",
    redis_password=os.getenv("REDIS_PASSWORD", "password"),
    redis_username=os.getenv("REDIS_USERNAME", "default"),
)

from base_dash_app.application.celery_decleration import CelerySingleton

celery_singleton: CelerySingleton = CelerySingleton.get_instance()
celery = celery_singleton.get_celery()
broker_use_ssl = celery_singleton.broker_use_ssl


rta = RuntimeApplication(my_app_descriptor)
rta.celery = celery
app = rta.app
server = rta.server
db_manager = rta.dbm
