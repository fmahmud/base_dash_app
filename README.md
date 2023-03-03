# base_dash_app

![example](https://github.com/fmahmud/base_dash_app/actions/workflows/python-package.yml/badge.svg)

Current version: 0.8.0

## Demo App Usage
If you are checking out this repository, you can use the Demo App as an example of 
how to setup your own Dash App using this package.

### App Descriptors and Running the App
The [`AppDescriptor`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/application/app_descriptor.py)
class exposes a number of properties that can be used to configure the Dash App.
The `RuntimeApplication` uses the information you have provided in the 
`AppDescriptor` to configure and run your Dash App.

This is the snippet from the Demo App that shows how to create an `AppDescriptor`.
```python
my_app_descriptor = AppDescriptor(
    db_descriptor=db_descriptor,
    title="Test App", external_stylesheets=external_stylesheets,
    views=[DemoView, AreaGraphView, AsyncDemoView], view_groups={"Test": [DemoView]},
    jobs=[TestJobDef], service_classes=[MySelectablesService],
    upgrade_db=True,
    drop_tables=True,
    use_auth=True,
    valid_user_pairs={"test": "test"},
    log_level=logging.WARN,
    alerts_refresh_timeout=2000,
    assets_folder_path="../base_dash_app/assets"
)
```

Breakdown of the `AppDescriptor` properties:
1) `db_descriptor`: The `DBDescriptor` class is used to configure the database connection.
2) `title`: The title of the Dash App.
3) `external_stylesheets`: A list of string URLs that point to CSS files you want to include.
4) `views`: The views to register with the Dash App. 
These should all be instances of the [`BaseView`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/views/base_view.py) class.
5) `view_groups`: The view groups to configure the navbar for your Dash App.
6) `jobs`: The jobs to register with the Dash App. 
These should all be instances of the [`JobDefinition`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/models/job_definition.py) class. 
7) `service_classes`: The service classes to register with the Dash App. 
These should all be instances of the [`BaseService`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/services/base_service.py) class.
8) `upgrade_db`: Whether or not to upgrade the database schema on startup.
9) `drop_tables`: Whether or not to drop the database tables on startup before upgrading the schema.
10) `use_auth`: Whether or not to use authentication for the Dash App.
11) `valid_user_pairs`: A dictionary of valid username/password pairs.
12) `log_level`: The log level to use for the Dash App.
13) `alerts_refresh_timeout`: The size of the interval in seconds between each refresh of the alerts section.
14) `assets_folder_path`: The path to the assets folder.

The following are more properties of the `AppDescriptor` class that aren't used in the demo:
1) `initial_global_state`: The initial global state to use for the Dash App.
2) `extra_nav_bar_components`: A list of Dash components to add to the navbar.
3) `global_inputs`: Deprecated
4) `logging_format`: The logging format to use for the Dash App.
5) `env_vars`: A dictionary of environment variables to use for the Dash App.
6) `env_file_location`: The location of the environment file to use for the Dash App.
7) `silence_routes_logging`: Whether or not to silence the logging of every http call to your Dash App.
8) `components_with_internal_callbacks`: A list of classes that extend the [`ComponentWithInternalCallback`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/components/base_component.py#L19)
class. These components will be registered with the Dash App and will be able to use the internal callback mechanism.

## Package Usage
1) Download the latest wheel from the [releases](https://github.com/fmahmud/base_dash_app/releases) page.
2) Install the wheel using `pip install <path_to_wheel>/base_dash_app-<version>-py3-none-any.whl`


## Repo Usage

### Requirements
`pip3 install twine setuptools wheel`

### Installation
`pip install <path_to_wheel>`

e.g. `pip install ./dist/base_dash_app-0.1.8-py3-none-any.whl`

### Uninstallation
`pip uninstall <path_to_wheel>`

e.g. `pip uninstall ./dist/base_dash_app-0.1.8-py3-none-any.whl`

### Generate Requirements
`pip3 freeze > requirements.txt`

### Package into wheel
` python setup.py bdist_wheel`
