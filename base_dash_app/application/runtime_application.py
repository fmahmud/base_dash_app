import traceback
from typing import List, Callable, Dict, Type, Union
from urllib.parse import unquote

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.components.navbar import NavBar
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.virtual_objects.interfaces.Startable import Startable, ExternalTriggerEvent


# todo: split these two classes and name the files app_descriptor and runtime_application


class RuntimeApplication:
    def __init__(self, app_descriptor: AppDescriptor):
        self.app_descriptor = app_descriptor

        self.app = dash.Dash(
            app_descriptor.title, external_stylesheets=app_descriptor.external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder='./base_dash_app/assets'
        )

        self.server = self.app.server
        self.dbm = None

        if app_descriptor.db_file is not None:
            self.dbm = DbManager(app_descriptor.db_file)

        # define services #
        self.services: Dict[Type, BaseService] = {}

        # define APIs
        # self.apis: Dict[Type, ]

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
            # todo: support custom components through app descriptor
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

    def run_server(self, debug=False, host="0.0.0.0", upgrade_db=False):
        if self.dbm is not None and upgrade_db:
            self.dbm.upgrade_db()

        for startable in Startable.STARTABLE_DICT[ExternalTriggerEvent.SERVER_START]:
            startable.start()

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
                ),
                # html.Div(
                #     id="alerts-div",
                #     style={
                #         "position": "fixed", "top": "30px", "width": "500px", "margin": "0 auto", "height": "400px",
                #         "zIndex": "90000"
                #     }
                # )
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
