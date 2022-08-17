import dash_bootstrap_components as dbc

from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.utils.db_utils import DbDescriptor, DbEngineTypes
from demo_app.demo_view import DemoView, TestJobDef

external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto&display=swap",
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
    dbc.themes.BOOTSTRAP
]

db_descriptor: DbDescriptor = DbDescriptor(
    db_uri="./temp.db",
    engine_type=DbEngineTypes.SQLITE
)

my_app_descriptor = AppDescriptor(
    db_descriptor=db_descriptor,
    title="Test App", external_stylesheets=external_stylesheets,
    views=[DemoView], view_groups={"Test": [DemoView]},
    jobs=[TestJobDef], upgrade_db=True,
    drop_tables=True,
    use_auth=True,
    valid_user_pairs={"test": "test"}
)

app = RuntimeApplication(my_app_descriptor)
app.run_server(debug=False, port=60000)