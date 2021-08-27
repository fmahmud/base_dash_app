import traceback
from typing import List, Callable, Dict, Type, Union
from urllib.parse import unquote

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.components.navbar import NavBar
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView


class AppDescriptor:
    """
    Used to define the service with as much granular control as needed.
    """
    def __init__(
        self, *, db_file: str, title: str = None, service_classes: List[Type[BaseService]] = None,
        external_stylesheets: List[str] = None, views: List[Type[BaseView]] = None,
    ):
        """
        :param db_file: Required - location of sqlite db file
        :param title: Optional - Title of app
        :param service_classes: Optional - list of all uninitialized service classes that extend BaseService
        :param external_stylesheets:
        :param views: Optional - List of all uninitialized view classes that extend BaseView that could be rendered in
            the app
        """

        if db_file is None:
            raise Exception("Can't start application without db_file")
        self.db_file: str = db_file
        self.title: str = title if title is not None else ""
        self.service_classes: List[Type[BaseService]] = service_classes if service_classes is not None else []
        self.external_stylesheets: List[str] = external_stylesheets if external_stylesheets is not None else []
        self.views: List[Type[BaseView]] = views if views is not None else []


class RuntimeApplication:
    def __init__(self, app_descriptor: AppDescriptor):
        self.app_descriptor = app_descriptor

        self.app = dash.Dash(
            app_descriptor.title, external_stylesheets=app_descriptor.external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder='./base_dash_app/assets'
        )

        self.server = self.app.server

        self.dbm = DbManager(app_descriptor.db_file)

        # define services #
        self.services: Dict[Type, BaseService] = {}

        def get_service_by_name(service_class: Type) -> BaseService:
            return self.services.get(service_class)

        base_service_args = {
            "dbm": self.dbm,
            "service_provider": get_service_by_name
        }

        self.services = {s: s(**base_service_args) for s in app_descriptor.service_classes}

        base_view_args = {
            "register_callback_func": self.register_callback,
            "dbm": self.dbm,
            "service_provider": get_service_by_name,
        }

        components_with_internal_callbacks = [
            TaskGroup
        ]

        # define pages
        self.pages = [p(**base_view_args) for p in app_descriptor.views]

        wrapped_get_handler = self.bind_to_self(self.handle_get_call)

        self.register_callback(
            output=Output('page-content', 'children'),
            inputs=[Input('url', 'pathname'), Input('url', 'search')],
            function=wrapped_get_handler,
            state=[]
        )

        for comp in components_with_internal_callbacks:
            callbacks = comp.get_callback_definitions()
            for cb in callbacks:
                self.register_callback(**cb)

        self.navbar = self.initialize_navbar()

        self.app.layout = self.get_layout

    def run_server(self, debug=False, host="0.0.0.0"):
        # self.dbm.upgrade_db()
        self.app.run_server(debug=debug, host=host)

    def initialize_navbar(self) -> NavBar:
        nav_items = []

        for page in self.pages:
            if page.show_in_navbar:
                nav_items.append(dbc.NavItem(
                    dbc.NavLink(
                        page.title,
                        href=page.nav_url,
                        external_link=False
                    ),
                    style={"fontSize": "16px"}
                ))

        return NavBar(title=self.app_descriptor.title, nav_items=nav_items)

    def get_layout(self):
        return html.Div(
            children=[
                dcc.Location(id="url", refresh=False),
                self.navbar.render(),
                html.Div(
                    id="page-content",
                    style={
                        "width": "90wh", "height": "100%", "padding": "20px",
                        "margin": "0 auto"
                    }
                )
            ],
            style={"fontFamily": "'Roboto', sans-serif"}
        )

    def register_callback(self, output: Union[Output, List[Output]], inputs: List[Input], state: List[State], function: Callable):
        self.app.callback(output=output, inputs=inputs, state=state)(function)

    def bind_to_self(self, func):
        bound_method = func.__get__(self, self.__class__)
        setattr(self, func.__name__, bound_method)
        return bound_method

    def handle_get_call(self, url: str, query_params: str):
        decoded_url = unquote(url)
        decoded_params = unquote(query_params)
        for page in self.pages:
            if page.matches(decoded_url):
                try:
                    return page.render(decoded_params)
                except Exception as e:
                    traceback.print_exc()
                    return html.Div("Page under construction")

        return html.Div("404 Not Found.")
