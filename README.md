# base_dash_app

![example](https://img.shields.io/github/actions/workflow/status/fmahmud/base_dash_app/python-package.yml?branch=master&style=for-the-badge)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/fmahmud/base_dash_app?color=green&style=for-the-badge)
![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/t/fmahmud/base_dash_app?style=for-the-badge&color=darkred)


## Setting Up Development Environment
### Dependencies
This package requires the following dependencies to be installed:
- Python 3.11
- Docker [Download Here](https://www.docker.com/)
- Precommit
  - ```pip3 install pre-commit```
- Pipenv:
  - ```pip3 install pipenv```

### Steps
1) Clone the repository
2) Create local virtual environment with ```pip3 -m venv venv```
3) Activate the virtual environment with ```source venv/bin/activate```
3) Run `pipenv install --dev`
4) Run `pre-commit install`
5) Run tests with `pipenv run pytest tests`

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
- **`std_out_formatter`** (`logging.Formatter`): Optional - Formatter to use for stdout
- **`disable_memory_capture`** (`bool`): If set to True, disables memory capture.
- **`health_endpoint_path`** (`str`): Path to the health endpoint.
- **`redis_host`** (`str`): Host of the redis instance.
- **`redis_port`** (`int`): Port of the redis instance.
- **`redis_db_number`** (`int`): DB of the redis instance.
- **`redis_use_ssl`** (`bool`): If set to True, uses SSL for the redis instance.
- **`redis_username`** (`str`): Username for the redis instance. Required if `redis_use_ssl` is True. Default is "default"
- **`redis_password`** (`str`): Password for the redis instance. Required if `redis_use_ssl` is True. Default is "password"

## Usage

### Dependencies
This package requires the following dependencies to be installed:
- Python 3.9
- Docker
  - [Download Here](https://www.docker.com/)
- Precommit
  - ```pip install pre-commit``` or ```pip3 install pre-commit```
  - ```pre-commit install```
- Pipenv:
  - ```pip install pipenv``` or ```pip3 install pipenv```
  - Activate the virtual environment: ```pipenv shell```
  - Install dev dependencies: ```pipenv install --dev```

### Docker
This package is designed to be used with Docker. 
To use the package, simply create a Dockerfile that looks like this:

```dockerfile
FROM python:3.9-slim-bookworm as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

USER root
# Install pipenv and compilation dependencies
RUN pip install --upgrade pip
RUN pip install pipenv
RUN apt-get update && apt-get install -y libpq5 gcc

# Install python dependencies in /.venv
COPY ./Pipfile .
COPY ./Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Create and switch to a new user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

COPY ./ ./

RUN pip install ./*.whl
```

### Docker Compose
Dash, which is based on Flask, is supposed to be run with a production WSGI server. In this case, we use Gunicorn.
In order to setup the app to run with Gunicorn, we use Docker Compose. Additionally, in order to support a larger
workload, we use Celery to run background tasks. The `docker-compose.yml` file should look like this:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "60000:60000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/testdb
      - CELERY_BROKER_URL=redis://redis:6379/0
    # IMPORTANT:
    # test_app:server is <name_of_file>:<name of server variable>
    command: ["gunicorn", "test_app:server", "-b", "0.0.0.0:60000"]  
    depends_on:
      - redis
      - db
  worker:
    build: .
    # IMPORTANT:
    # celery_app:celery is <name_of_file>:<name of celery variable>
    command: celery -A celery_app.celery worker --loglevel=info --pool threads
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/testdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - web
      - redis
      - db
  beat:
    build: .
    # IMPORTANT:
    # celery_app:celery is <name_of_file>:<name of celery variable>
    command: celery -A celery_app.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/testdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - web
      - redis
      - db
  redis:
    image: "redis:alpine"
    ports:
      - "6379:6379"
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
```

> **Important Note**: This will expose your server at port 60000 on your localhost. 
> If you want to expose it at a different port, change the first port number in the `web` service.
> 
> **Additionally**, If you want to access any of these services like the DB or redis directly, 
> you can go to `localhost:5432` or `localhost:6379` respectively. 


If you want to preserve the DB between runs, you can mount a volume to the DB container:
```yaml
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Executing the Demo App
1) `cd` into the `demo_app` directory
2) Run `docker-compose up --build`
3) Use the app at `localhost:60000`
4) Bring the app down with `docker-compose down` in another terminal (while in the same directory) or `ctrl+c` and then `docker-compose down`
5) If you want to bring the app down and remove the database, run `docker-compose down -v`
6) If you want to bring the app down and remove the database and the images, run `docker-compose down -v --rmi all`

## Code Structure
### Models
### Services
### Views
### APIs
### Jobs
### Environment Variables
### Components
### Initializing Your Own App
#### Install the wheel
> ```pipenv install https://github.com/fmahmud/base_dash_app/releases/download/0.9.13/base_dash_app-0.9.13-py3-none-any.whl```
>
> or whatever the latest [release is](https://github.com/fmahmud/base_dash_app/releases)

#### Import base_dash_app
```python
from base_dash_app.application.runtime_application import RuntimeApplication
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.utils.db_utils import DbDescriptor, DbEngineTypes
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
from base_dash_app.utils.log_formatters.colored_formatter import ColoredFormatter
```

#### Configure the App
To utilize the `AppDescriptor` class, simply instantiate it with desired parameters. Here is are two snippets from the
Demo App (in `demo_app/test_app.py`):

To specify the database to use, you can use the `DbDescriptor` class:

**_DB Descriptor_**
```python
db_descriptor: DbDescriptor = DbDescriptor(
    db_uri="db:5432/testdb",
    engine_type=DbEngineTypes.POSTGRES,
    username="postgres",
    password="password",
)
```

**_App Descriptor_**
```python
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
)
```
#### Running the App
>  **Note**:
> - If you are using celery, you need to make the celery instance available as a global variable. 
> - If you are using gunicorn, you need to make the `rta.server` (the Flask App) available as a global variable.
> - If you are using gunicorn in local, you can set `server.config["TESTING"] = True` to enable testing mode. This will print out uncaught exception stacktraces

```python
rta = RuntimeApplication(my_app_descriptor)
app = rta.app
server = rta.server
server.config["TESTING"] = True
db_manager = rta.dbm
```

As you might notice, we are passing in a separate file to run celery in our docker-compose file. 
That is because we want the Celery worker to have access to the `RuntimeApplication` instance, but not 
make any changes to the database. In order to do that, we need to instantiate a slightly different version of 
the `RuntimeApplication` instance for celery:

```python
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
```
>>> Assuming all else is in place, you can run the app with `docker-compose up --build` and access it at `localhost:60000`.

---


## Developing the Wheel

#### Update version in `setup.py`
```python
from setuptools import find_packages, setup
setup(
    name='base_dash_app',
    packages=find_packages(),
    version='0.10.0',
    description='Base Dash Webapp',
    author='fmahmud',
    license='MIT',
)
```

#### Package into wheel
```
pipenv run python setup.py bdist_wheel
```


## Migrating from 0.9.13 to 0.10.0
### App execution (Docker, Docker Compose, Gunicorn, Celery, Redis, Env Vars)
1) Celery, Redis, FlaskSQLAlchemy are all required dependencies now
2) You should create a separate file for celery execution (e.g. celery_app) to handle the following (see [Running the App](#running-the-app))
   1) Celery instance needs to be available as a global variable
   2) Server (Flask App) instance needs to be available as a global variable
3) For Gunicorn, you need to expose the server instance as a global variable
4) Make sure the "CELERY_BROKER_URL" environment variable is set to whatever your redis URL is
   1) e.g. "redis://redis:6379/0" in your docker-compose file
5) Make sure the "REDIS_URL" environment variable is set to whatever your redis URL is
   1) e.g. "redis://redis:6379/0" in your docker-compose file

### General Model Life Cycle
1) Don't store references to the model at the view or service instance level. Instead, store the ID of that model
and fetch it every time from the DB and pass it to your render functions. This is because you can't assume
which thread will be serving the request and it will likely be detached from any session as a result.

### App Setup (App Descriptor, DB Descriptor, Runtime Application)
1) no longer accepts interval seconds being set for scheduler
2) You might have been using SQLite before in local, now you need to use Postgres which is setup within the
docker compose file for local. You might have had a piece of code like this:
```python
if IS_LOCAL:
    db_descriptor: DbDescriptor = DbDescriptor(
        db_uri="./temp.db",
        engine_type=DbEngineTypes.SQLITE,
    )
...
```
You need to change it to this:
> **Important Note**: This must be done in all your entry point files (e.g. celery_app.py, test_app.py, etc.) 
```python
if IS_LOCAL:
    db_descriptor: DbDescriptor = DbDescriptor(
        db_uri="db:5432/testdb",
        engine_type=DbEngineTypes.POSTGRES,
        username="postgres",
        password="password",
    )
...
```
3) 

### DB Manager:
1) DB manager instances should now be entered and exited:
```python
with self.dbm as dbm:
    session: Session = dbm.get_session()
    ... # all code that uses session.
```

### Services
1) All services **can** take a session as an optional parameter to use for all DB operations:
```python
with self.dbm as dbm:
    session: Session = dbm.get_session()
    my_models = self.service.get_all(session)
```
if no session is provided, it will get the session for the DB Manager instance

### ComponentsWithInternalCallback
1) Should now be defined as instance variables and passed to raw_render functions
instead of being instantiated within raw render files
2) 

### Job Definitions
1) Previously, Job Definitions could be setup to have parameters that take in an instance of a selectable.
These parameters would be shown in the job card as individual dropdowns. 
Now, you can set the job definition to be a "Single Selectable" job definition. 
This means it requires only one selectable as a parameter. With this change, instead of showing the selectables
in a drop down, the Job Card will now show a run button and progress bar for each selectable. In order to use this
you have to setup a few  additional functions:
   1) Add the following methods:
```python
class TestJobDef(JobDefinition):

    @classmethod
    def get_selectable_type(cls) -> Optional[Type[Selectable]]:
        return MySelectableModel

    @classmethod
    def single_selectable_param_name(cls) -> Optional[str]:
        return "param_4"

    @classmethod
    def get_latest_exec_for_selectable(cls, selectable: Selectable, session: Session) -> Optional[JobInstance]:
        param_substring = f"\"{cls.single_selectable_param_name()}\": {selectable.get_value()}"

        instance: JobInstance = (
            session.query(JobInstance)
            .filter(JobInstance.job_definition_id == cls.id)
            .filter(JobInstance.start_time.isnot(None))
            .filter(or_(
                JobInstance.parameters.like(f"%, {param_substring},%"),
                JobInstance.parameters.like("{" + f"{param_substring}" + "}%")
            ))
            .order_by(JobInstance.start_time.desc())
            .first()
        )

        return instance

    @classmethod
    def get_selectables_by_param_name(
            cls, variable_name, session: Session
    ) -> List[CachedSelectable]:
        if variable_name == "param_4":
            return session.query(MySelectableModel).all()
            

    
    """ the rest of your code """
```

3) Use `prog_container.set_progress(progress)` to update the progress and push to redis. 
Just incrementing progress will only affect the local progress value
3) 


# Troubleshooting
1) `db_1      | initdb: error: could not create directory "/var/lib/postgresql/data/pg_wal": No space left on device`
   - This can be due to having multiple docker containers running with the same DB configuration, causing a conflict.
   - Or because there are too many volumes present. Try running:
   - `docker-compose down -v` to remove all volumes. This might have to be run in other repos as well.