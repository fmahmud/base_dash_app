# base_dash_app

![example](https://img.shields.io/github/actions/workflow/status/fmahmud/base_dash_app/python-package.yml?branch=master&style=for-the-badge)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/fmahmud/base_dash_app?color=green&style=for-the-badge)


## Demo App Usage
If you are checking out this repository, you can use the Demo App as an example of 
how to setup your own Dash App using this package.

### App Descriptors and Running the App
The [`AppDescriptor`](https://github.com/fmahmud/base_dash_app/blob/master/base_dash_app/application/app_descriptor.py)
class exposes a number of properties that can be used to configure the Dash App.
The `RuntimeApplication` uses the information you have provided in the 
`AppDescriptor` to configure and run your Dash App.
Sure, I'll create a markdown documentation for the `AppDescriptor` class:

---

# AppDescriptor Class

`AppDescriptor` is utilized for defining a service with customizable granularity. The class offers various parameters to cater to different needs of a service.

## Initialization Parameters

### Main Parameters

- **`db_descriptor`** (`DbDescriptor`): Descriptor of the database to use.
- **`title`** (`str`): The title of the application. Default is an empty string.
- **`service_classes`** (`List[Type[BaseService]]`): List of all uninitialized service classes that extend `BaseService`. Default is an empty list.
- **`external_stylesheets`** (`List[str]`): External stylesheets to be used. Default is an empty list.
- **`views`** (`List[Type[BaseView]]`): List of uninitialized view classes extending `BaseView` that could be rendered in the app. Default is an empty list.

### Optional Parameters

- **`initial_global_state`** (`Dict`): Sets the initial global state in the global state service. Default is an empty dictionary.
- **`extra_nav_bar_components`** (`List`): Appends any provided rendered components to the right side of the nav bar. Default is an empty list.
- **`global_inputs`** (`List[InputToState]`): List of global inputs.
- **`view_groups`** (`Dict[str, List[Type[BaseView]]]`): Group of views to be used.
- **`apis`** (`List[Type[API]]`): List of APIs to be used in the app. Default is an empty list.
- **`logging_format`** (`str`): Logging format to be used.
- **`log_level`** (`str`): Logging level to be set.
- **`jobs`** (`List[Type[JobDefinition]]`): List of jobs for the application. Default is an empty list.
- **`upgrade_db`** (`bool`): Flag to indicate if the database should be upgraded.
- **`env_vars`** (`List[EnvVarDefinition]`): List of environment variables for the application. Default is an empty list.
- **`env_file_location`** (`str`): Location of the environment file.
- **`drop_tables`** (`bool`): If set to True, drops all tables in the database before creating them.
- **`use_auth`** (`bool`): If set to True, uses basic authentication to protect the app.
- **`valid_user_pairs`** (`Dict[str, str]`): If `use_auth` is True, this is a dictionary of valid `username:password` pairs. Default is an empty dictionary.
- **`silence_routes_logging`** (`bool`): If set to True, silences the logging of every call to routes.
- **`alerts_refresh_timeout`** (`int`): How often the alerts refresh in milliseconds.
- **`assets_folder_path`** (`str`): Path to the assets folder.
- **`components_with_internal_callbacks`** (`List[Type[ComponentWithInternalCallback]]`): List of components that have internal callbacks.
- **`use_scoped_session`** (`bool`): If set to True, uses a scoped session for the database.
- **`max_num_threads`** (`int`): Maximum number of threads to use for the app.
- **`scheduler_interval_seconds`** (`int`): Interval in seconds for the background scheduler to run at.

## Usage

To utilize the `AppDescriptor` class, simply instantiate it with desired parameters:

```python
app_descriptor = AppDescriptor(
    title="My App",
    service_classes=[MyService],
    views=[MyView],
    ...
)
```

---


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
