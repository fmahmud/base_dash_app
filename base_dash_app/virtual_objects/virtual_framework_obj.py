import logging
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from base_dash_app.utils.db_utils import DbManager


class VirtualFrameworkObject:
    def __init__(self, *args, **kwargs):
        self.dbm: Optional['DbManager'] = kwargs["dbm"] if "dbm" in kwargs else None
        self.get_service = kwargs["service_provider"] if "service_provider" in kwargs else None
        self.get_api = kwargs["api_provider"] if "api_provider" in kwargs else None
        self.all_apis = kwargs["all_apis"] if "all_apis" in kwargs else None
        self.register_callback_func = kwargs["register_callback_func"] if "register_callback_func" in kwargs else None
        self.push_alert = kwargs["push_alert"] if "push_alert" in kwargs else None
        self.remove_alert = kwargs["remove_alert"] if "remove_alert" in kwargs else None
        self.env_vars = kwargs["env_vars"] if "env_vars" in kwargs else None
        self.logger = logging.getLogger(kwargs["logger_name"] if "logger_name" in kwargs else self.__class__.__name__)
        self.get_view = kwargs["view_provider"] if "view_provider" in kwargs else None

    def produce_kwargs(self):
        return {
            "dbm": self.dbm,
            "service_provider": self.get_service,
            "api_provider": self.get_api,
            "all_apis": self.all_apis,
            "register_callback_func": self.register_callback_func,
            "push_alert": self.push_alert,
            "remove_alert": self.remove_alert,
            "env_vars": self.env_vars,
            "view_provider": self.get_view,
        }

    def set_vars_from_kwargs(self, **kwargs):
        self.dbm: Optional['DbManager'] = kwargs["dbm"] if "dbm" in kwargs else None
        self.get_service = kwargs["service_provider"] if "service_provider" in kwargs else None
        self.get_api = kwargs["api_provider"] if "api_provider" in kwargs else None
        self.all_apis = kwargs["all_apis"] if "all_apis" in kwargs else None
        self.register_callback_func = kwargs["register_callback_func"] if "register_callback_func" in kwargs else None
        self.push_alert = kwargs["push_alert"] if "push_alert" in kwargs else None
        self.remove_alert = kwargs["remove_alert"] if "remove_alert" in kwargs else None
        self.env_vars = kwargs["env_vars"] if "env_vars" in kwargs else None
        self.get_view = kwargs["view_provider"] if "view_provider" in kwargs else None
