import logging

import dash_bootstrap_components as dbc
from dash_bootstrap_components.icons import FONT_AWESOME

from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.utils.db_utils import DbDescriptor, DbEngineTypes
from demo_app.async_demo_view import AsyncDemoView
from demo_app.demo_view import DemoView, TestJobDef, MySelectablesService
from demo_app.area_graph_view import AreaGraphView

external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto&display=swap",
    dbc.themes.BOOTSTRAP,
    FONT_AWESOME
]

db_descriptor: DbDescriptor = DbDescriptor(
    db_uri="./temp.db",
    engine_type=DbEngineTypes.SQLITE
)

my_app_descriptor = AppDescriptor(
    db_descriptor=db_descriptor,
    title="Test App", external_stylesheets=external_stylesheets,
    views=[DemoView, AreaGraphView, AsyncDemoView], view_groups={"Test": [DemoView]},
    jobs=[TestJobDef], service_classes=[MySelectablesService],
    upgrade_db=True,
    drop_tables=True,
    use_auth=True,
    valid_user_pairs={"test": "test"},
    log_level=logging.INFO,
    alerts_refresh_timeout=2000,
    assets_folder_path="../base_dash_app/assets",
    scheduler_interval_seconds=60,
)

app = RuntimeApplication(my_app_descriptor)
app.run_server(debug=False, port=60000)