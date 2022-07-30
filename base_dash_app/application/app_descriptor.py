from typing import List, Type, Hashable, Any, Dict

from base_dash_app.apis.api import API
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
from base_dash_app.views.base_view import BaseView
from base_dash_app.models.job_definition import JobDefinition


class AppDescriptor:
    """
    Used to define the service with as much granular control as needed.
    """
    def __init__(
        self, *,
            title: str = None,
            service_classes: List[Type[BaseService]] = None,
            external_stylesheets: List[str] = None,
            views: List[Type[BaseView]] = None,
            db_file: str = None,
            initial_global_state: Dict[Hashable, Any] = None,
            extra_nav_bar_components: List = None,
            global_inputs: List[InputToState] = None,
            view_groups: Dict[str, List[Type[BaseView]]] = None,
            apis: List[Type[API]] = None,
            logging_format=None,
            log_level=None,
            jobs: List[Type[JobDefinition]] = None,
            upgrade_db=False,
            env_vars: List[EnvVarDefinition] = None
    ):
        """
        :param db_file: Optional - location of an sqlite db file
        :param title: Optional - Title of app
        :param service_classes: Optional - list of all uninitialized service classes that extend BaseService
        :param external_stylesheets:
        :param views: Optional - List of all uninitialized view classes that extend BaseView that could be rendered in
            the app
        :param initial_global_state: Sets the initial global state in the global state service
        :param extra_nav_bar_components: Appends any provided rendered components to the right side of the nav bar
        """

        self.db_file: str = db_file
        self.title: str = title if title is not None else ""
        self.service_classes: List[Type[BaseService]] = service_classes if service_classes is not None else []
        self.external_stylesheets: List[str] = external_stylesheets if external_stylesheets is not None else []
        self.views: List[Type[BaseView]] = views if views is not None else []
        self.initial_global_state = {} if initial_global_state is None else initial_global_state
        self.extra_nav_bar_components = extra_nav_bar_components if extra_nav_bar_components is not None else []
        self.global_inputs: List[InputToState] = global_inputs if global_inputs is not None else []
        self.view_groups: Dict[str, List[Type[BaseView]]] = view_groups if view_groups is not None else {}
        self.apis: List[Type[API]] = apis if apis is not None else []
        self.logging_format = logging_format
        self.log_level = log_level
        self.jobs: List[Type[JobDefinition]] = jobs if jobs is not None else []
        self.upgrade_db = upgrade_db
        self.env_vars = env_vars if env_vars is not None else []
