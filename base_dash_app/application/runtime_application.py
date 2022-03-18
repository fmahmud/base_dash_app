import traceback
from typing import List, Callable, Dict, Type, Union
from urllib.parse import unquote

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

from base_dash_app.apis.api import API
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.components.callback_utils.utils import get_triggering_id_from_callback_context, \
    get_state_values_for_input_from_args_list
from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.components.navbar import NavBar, NavDefinition, NavGroup
from base_dash_app.services.base_service import BaseService
from base_dash_app.services.global_state_service import GlobalStateService
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.interfaces.Startable import Startable, ExternalTriggerEvent


class RuntimeApplication:
    def __init__(self, app_descriptor: AppDescriptor):
        from base_dash_app.utils.logger_utils import configure_logging
        configure_logging(
            logging_format=app_descriptor.logging_format,
            log_level=app_descriptor.log_level
        )

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

        # define services
        self.services: Dict[Type, BaseService] = {}

        def get_service_by_name(service_class: Type) -> BaseService:
            return self.services.get(service_class)

        self.apis: Dict[Type, API] = {}
        for api_type in app_descriptor.apis:
            self.apis[api_type] = api_type()

        def get_api_by_name(api_class: Type) -> API:
            return self.apis.get(api_class)

        base_service_args = {
            "dbm": self.dbm,
            "service_provider": get_service_by_name,
            "api_provider": get_api_by_name
        }

        self.services = {s: s(**base_service_args) for s in app_descriptor.service_classes}
        self.services[GlobalStateService] = GlobalStateService(initial_state=app_descriptor.initial_global_state)

        base_view_args = {
            "register_callback_func": self.register_callback,
            **base_service_args
        }

        # components_with_internal_callbacks = [
        #     # todo: support custom components through app descriptor
        #     TaskGroup
        # ]

        # define pages
        self.pages = [p(**base_view_args) for p in app_descriptor.views]

        wrapped_get_handler = self.bind_to_self(self.handle_get_call)

        self.__global_inputs = app_descriptor.global_inputs
        self.__global_input_string_ids_map = {its.get_input_string_id(): its for its in self.__global_inputs}
        resulting_inputs = [Input('url', 'pathname'), Input('url', 'search')]
        resulting_states = []
        for g_input in app_descriptor.global_inputs:
            g_input: InputToState
            resulting_inputs.append(g_input.input.get_as_input())
            resulting_states += [s.get_as_state() for s in g_input.states]

        self.register_callback(
            output=Output('page-content', 'children'),
            inputs=resulting_inputs,
            function=wrapped_get_handler,
            state=resulting_states
        )

        # for comp in components_with_internal_callbacks:
        #     callbacks = comp.get_callback_definitions()
        #     for cb in callbacks:
        #         self.register_callback(**cb)

        self.navbar = self.initialize_navbar(app_descriptor.extra_nav_bar_components, app_descriptor.view_groups)

        self.app.layout = self.get_layout

    def run_server(self, debug=False, host="0.0.0.0", upgrade_db=False):
        if self.dbm is not None and upgrade_db:
            self.dbm.upgrade_db()

        for startable in Startable.STARTABLE_DICT[ExternalTriggerEvent.SERVER_START]:
            startable.start()

        self.app.run_server(debug=debug, host=host)

    def initialize_navbar(self, extra_components: List, view_groups: Dict[str, List[Type[BaseView]]]) -> NavBar:
        nav_items = []

        pages_to_ignore = set()
        nav_groups: List[NavGroup] = []
        page_to_nav_group: Dict[Type[BaseView], NavGroup] = {}
        for k, v in view_groups.items():
            pages_to_ignore.update(set(v))  # add new page types
            nav_group: NavGroup = NavGroup(k)  # create new nav group
            nav_groups.append(nav_group)  # add to list
            for page in v:
                page_to_nav_group[page] = nav_group  # add to mapping to go the other way

        for page in self.pages:
            if page.show_in_navbar:
                if type(page) in page_to_nav_group:
                    nav_group: NavGroup = page_to_nav_group[type(page)]
                    nav_group.add_nav(NavDefinition(label=page.title, url=page.nav_url))
                else:
                    nav_items.append(
                        NavDefinition(label=page.title, url=page.nav_url).render()
                    )

        return NavBar(
            title=self.app_descriptor.title,
            nav_items=nav_items,
            nav_groups=nav_groups,
            extra_components=extra_components
        )

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
                # todo - global alerts div (issue #16)
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

    def handle_get_call(self, url: str, query_params: str, *args):
        triggering_id, index = get_triggering_id_from_callback_context(dash.callback_context)

        actual_id = None
        for k in self.__global_input_string_ids_map.keys():
            if triggering_id.startswith(k):
                actual_id = k
                break

        if actual_id is not None:
            states_for_input = get_state_values_for_input_from_args_list(
                input_id=actual_id, input_string_ids_map=self.__global_input_string_ids_map, args_list=args
            )
        else:
            states_for_input = {}

        decoded_url = unquote(url)
        decoded_params = unquote(query_params)
        for page in self.pages:
            if page.matches(decoded_url):
                try:
                    return page.render(decoded_params, states_for_input)
                except Exception as e:
                    traceback.print_exc()
                    return html.Div("Page under construction")

        return html.Div("404 Not Found.")
