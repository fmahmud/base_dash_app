from abc import ABC, abstractmethod
from typing import Pattern, Callable

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.utils.db_utils import DbManager


class BaseView(BaseComponent, ABC):
    VIEWS = []

    def __init__(self, title: str, url_regex: Pattern[str],
                 register_callback_func: Callable, dbm: DbManager,
                 nav_url: str = "", show_in_navbar: bool = True,
                 service_provider: Callable = None):
        self.title = title,
        self.url_regex = url_regex
        self.path_params = {}
        self.nav_url = nav_url
        self.show_in_navbar = show_in_navbar
        self.register_callback_func = register_callback_func
        self.get_service = service_provider
        self.dbm = dbm

        if self not in BaseView.VIEWS:
            BaseView.VIEWS.append(self)

    # todo: move path params out of here. make it a return variable and have it sent to render function
    def matches(self, target_url: str):
        self.path_params = {}
        match_result = self.url_regex.match(target_url)
        if match_result is None:
            return False
        self.path_params = match_result.groupdict()
        return True

    @staticmethod
    @abstractmethod
    def raw_render(*args, **kwargs):
        pass


