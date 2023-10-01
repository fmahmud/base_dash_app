from typing import List, Type, Hashable, Any, Dict

from base_dash_app.apis.api import API
from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.db_utils import DbDescriptor
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
from base_dash_app.views.base_view import BaseView


class AppDescriptor:

    """
    Used to define the service with as much granular control as needed.
    """
    def __init__(
        self, *,
            title: str = None,
            service_classes: List[Type['BaseService']] = None,
            external_stylesheets: List[str] = None,
            views: List[Type['BaseView']] = None,
            db_descriptor: DbDescriptor = None,
            initial_global_state: Dict[Hashable, Any] = None,
            extra_nav_bar_components: List = None,
            global_inputs: List[InputToState] = None,
            view_groups: Dict[str, List[Type['BaseView']]] = None,
            apis: List[Type['API']] = None,
            logging_format=None,
            log_level=None,
            jobs: List[Type['JobDefinition']] = None,
            upgrade_db=False,
            env_vars: List[EnvVarDefinition] = None,
            env_file_location: str = None,
            drop_tables: bool = False,
            use_auth: bool = None,
            valid_user_pairs: Dict[str, str] = None,
            silence_routes_logging: bool = True,
            alerts_refresh_timeout: int = 1000,
            assets_folder_path: str = None,
            components_with_internal_callbacks: List[Type['ComponentWithInternalCallback']] = None,
            use_scoped_session: bool = False,
            max_num_threads: int = 5,
            std_out_formatter=None,
            disable_memory_capture: bool = True,
            health_endpoint_path: str = "/healthz",
            redis_host: str = None,
            redis_port: int = None,
            redis_db_number: int = None,
            redis_use_ssl: bool = False,
            redis_username: str = None,
            redis_password: str = None,
    ):
        """
        :param global_inputs: 
        :param view_groups: 
        :param apis: 
        :param logging_format: 
        :param log_level: 
        :param jobs: 
        :param upgrade_db: 
        :param env_vars: 
        :param env_file_location: 
        :param db_descriptor: Optional - Descriptor of the db to use
        :param title: Optional - Title of app
        :param service_classes: Optional - list of all uninitialized service classes that extend BaseService
        :param external_stylesheets:
        :param views: Optional - List of all uninitialized view classes that extend BaseView that could be rendered in
            the app
        :param initial_global_state: Sets the initial global state in the global state service
        :param extra_nav_bar_components: Appends any provided rendered components to the right side of the nav bar
        :param drop_tables: If True, drops all tables in the db before creating them
        :param use_auth: If True, uses basic auth to protect the app
        :param valid_user_pairs: If use_auth is True, this is a dict of valid username:password pairs
        :param silence_routes_logging: If True, silences the logging of every call to routes
        :param alerts_refresh_timeout: How often the alerts refresh in milliseconds
        :param assets_folder_path: Path to the assets folder
        :param components_with_internal_callbacks: List of components that have internal callbacks
        :param use_scoped_session: If True, uses a scoped session for the db
        :param max_num_threads: Max number of threads to use for the app
        :param std_out_formatter: Optional - Formatter to use for stdout
        :param disable_memory_capture: If True, disables memory capture
        :param health_endpoint_path: Path to the health endpoint
        :param redis_host: Host of the redis server
        :param redis_port: Port of the redis server
        :param redis_db_number: DB number of the redis server
        :param redis_use_ssl: If True, uses SSL for the redis server
        :param redis_username: Username for the redis server. Required if redis_use_ssl is True. Default value is "default"
        :param redis_password: Password for the redis server. Required if redis_use_ssl is True. Default value is "password"
        """

        self.db_descriptor: DbDescriptor = db_descriptor
        self.title: str = title or ""
        self.service_classes: List[Type[BaseService]] = service_classes or []
        self.external_stylesheets: List[str] = external_stylesheets or []
        self.views: List[Type[BaseView]] = views or []
        self.initial_global_state = initial_global_state or {}
        self.extra_nav_bar_components = extra_nav_bar_components or []
        self.global_inputs: List[InputToState] = global_inputs or []
        self.view_groups: Dict[str, List[Type[BaseView]]] = view_groups or {}
        self.apis: List[Type[API]] = apis or []
        self.logging_format = logging_format
        self.log_level = log_level
        self.jobs: List[Type[JobDefinition]] = jobs or []
        self.upgrade_db = upgrade_db
        self.env_vars: List[EnvVarDefinition] = env_vars or []
        self.env_file_location: str = env_file_location
        self.drop_tables: bool = drop_tables
        self.use_auth: bool = use_auth
        self.valid_user_pairs: Dict[str, str] = valid_user_pairs or {}
        self.silence_routes_logging: bool = silence_routes_logging
        self.alerts_refresh_timeout: int = alerts_refresh_timeout
        self.assets_folder_path: str = assets_folder_path
        self.components_with_internal_callbacks = components_with_internal_callbacks or []
        self.use_scoped_session: bool = use_scoped_session
        self.max_num_threads: int = max_num_threads
        self.std_out_formatter = std_out_formatter
        self.disable_memory_capture = disable_memory_capture
        self.health_endpoint_path = health_endpoint_path
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db_number = redis_db_number
        self.redis_use_ssl = redis_use_ssl
        self.redis_username = redis_username
        self.redis_password = redis_password