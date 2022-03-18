import dash_bootstrap_components as dbc

from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from demo_app.demo_view import DemoView

external_stylesheets = [
    "https://fonts.googleapis.com/css?family=Roboto&display=swap",
    'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
    dbc.themes.BOOTSTRAP
]

my_app_descriptor = AppDescriptor(
    db_file="./temp.db", title="Test App", external_stylesheets=external_stylesheets,
    views=[DemoView], view_groups={"Test": [DemoView]}
)

app = RuntimeApplication(my_app_descriptor)
app.run_server(debug=False)