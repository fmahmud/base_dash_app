import traceback
from typing import List, Callable, Dict, Type, Union
from urllib.parse import unquote

import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State, ALL
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session

from base_dash_app.apis.api import API
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.components import alerts
from base_dash_app.components.alerts import Alert
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.components.callback_utils.utils import get_triggering_id_from_callback_context, \
    get_state_values_for_input_from_args_list, invalid_n_clicks
from base_dash_app.components.cards.special_cards.job_card import JobCard
from base_dash_app.components.lists.todo_list.todo_list_item import TaskGroup
from base_dash_app.components.navbar import NavBar, NavDefinition, NavGroup
from base_dash_app.services.base_service import BaseService
from base_dash_app.services.global_state_service import GlobalStateService
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.interfaces.startable import Startable, ExternalTriggerEvent
from base_dash_app.models.job_definition import JobDefinition

ALERTS_WRAPPER_INTERVAL_ID = "alerts-wrapper-interval-id"

ALERTS_WRAPPER_DIV_ID = "alerts-wrapper-div-id"


class RuntimeApplication:
    def __init__(self, app_descriptor: AppDescriptor):
        from base_dash_app.utils.logger_utils import configure_logging
        configure_logging(
            logging_format=app_descriptor.logging_format,
            log_level=app_descriptor.log_level
        )

        self.app_descriptor = app_descriptor

        self.app = dash.Dash(
            title=app_descriptor.title, external_stylesheets=app_descriptor.external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder='./base_dash_app/assets'
        )

        self.server = self.app.server
        self.dbm = None

        self.active_alerts: List[Alert] = []
        self.services: Dict[Type, BaseService] = {}
        self.apis: Dict[Type, API] = {}
        self.views: List[BaseView] = []

        def push_new_alert(alert: Alert):
            if type(alert) != Alert:
                raise Exception(f"Trying to push alert of incorrect type: {type(alert)}.")
            self.active_alerts.append(alert)

        def remove_alert(alert: Alert):
            if alert is not None and alert in self.active_alerts:
                self.active_alerts.remove(alert)

        def get_service_by_type(service_class: Type) -> BaseService:
            return self.services.get(service_class)

        def get_api_by_type(api_class: Type) -> API:
            return self.apis.get(api_class)

        def get_all_apis() -> Dict[Type, API]:
            return self.apis

        if app_descriptor.db_file is not None:
            self.dbm = DbManager(app_descriptor.db_file)

        if self.dbm is not None and app_descriptor.upgrade_db:
            self.dbm.upgrade_db()

        base_service_args = {
            "dbm": self.dbm,
            "service_provider": get_service_by_type,
            "api_provider": get_api_by_type,
            "all_apis": get_all_apis,
            "register_callback_func": self.register_callback,
            "push_alert": push_new_alert,
            "remove_alert": remove_alert,
        }

        for api_type in app_descriptor.apis:
            self.apis[api_type] = api_type(**base_service_args)  # parent constructor vars will come from child

        job_def_service: JobDefinitionService = JobDefinitionService(**base_service_args)
        all_jobs_from_db: List[JobDefinition] = job_def_service.get_all()
        all_job_classes = set([type(jd) for jd in all_jobs_from_db])

        required_job_to_class_map = {job_type.__name__: job_type for job_type in app_descriptor.jobs}

        for class_name, job_class in required_job_to_class_map.items():
            if issubclass(job_class, JobDefinition) and job_class.autoinitialize():
                if job_class not in all_job_classes:
                    # job was never saved to DB and it should be autoinitialized
                    job = job_class.construct_instance(**base_service_args)
                    job_def_service.save(job)

                    all_jobs_from_db.append(job)
                    all_job_classes.add(job_class)
                elif job_class.force_update():

                    pass

        for s in app_descriptor.service_classes:
            self.services[s] = s(**base_service_args)

        self.services[GlobalStateService] = GlobalStateService(initial_state=app_descriptor.initial_global_state)
        self.services[JobDefinitionService] = job_def_service

        base_view_args = base_service_args

        for view in app_descriptor.views:
            self.views.append(view(**base_view_args))

        # components_with_internal_callbacks = [
        #     # todo: support custom components through app descriptor
        #     TaskGroup
        # ]

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

        self.register_callback(
            output=Output(ALERTS_WRAPPER_DIV_ID, "children"),
            inputs=[
                Input({"type": alerts.DISMISS_ALERT_BTN_ID, "index": ALL}, "n_clicks"),
                Input(ALERTS_WRAPPER_INTERVAL_ID, "n_intervals"),
                Input(alerts.CLEAR_ALL_ALERTS_BTN_ID, "n_clicks"),
            ],
            state=[],
            function=self.bind_to_self(self.handle_alerts)
        )

        # register internal callback components
        components_with_internal_callbacks = [JobCard]
        for comp_class in components_with_internal_callbacks:
            comp_class.do_registrations(self.register_callback)

        self.navbar = self.initialize_navbar(app_descriptor.extra_nav_bar_components, app_descriptor.view_groups)

        self.app.layout = self.get_layout

    def handle_alerts(self, n_clicks, n_interval, clear_all_nclicks, *args, **kwargs):
        if invalid_n_clicks(n_clicks) and invalid_n_clicks(n_interval)\
                and invalid_n_clicks(clear_all_nclicks):
            raise PreventUpdate()

        trigerring_id, index = get_triggering_id_from_callback_context(dash.callback_context)
        if trigerring_id.startswith(alerts.DISMISS_ALERT_BTN_ID):
            alert_to_dismiss = None
            for alert in self.active_alerts:
                if alert.id == index:
                    alert_to_dismiss = alert
                    break

            if alert_to_dismiss is None:
                raise PreventUpdate("Couldn't find alert with id %i" % index)

            self.active_alerts.remove(alert_to_dismiss)
        elif trigerring_id.startswith(alerts.CLEAR_ALL_ALERTS_BTN_ID):
            self.active_alerts.clear()

        return [
            alerts.render_alerts_div(self.active_alerts)
        ]

    def run_server(self, debug=False, host="0.0.0.0", port=8050, **kwargs):
        for startable in Startable.STARTABLE_DICT[ExternalTriggerEvent.SERVER_START]:
            startable.start()
        try:
            self.app.run_server(debug=debug, host=host, port=port)
        except:
            raise
        finally:
            self.dbm.session.close_all()

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

        for page in self.views:
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
                    children=alerts.render_alerts_div(
                        self.active_alerts,
                        wrapper_style={} if len(self.active_alerts) > 0 else {"display": "none"}
                    ),
                    id=ALERTS_WRAPPER_DIV_ID,
                    style={
                        "zIndex": "10000", "position": "absolute", "right": "0", "top": "60px",
                        "width": "580px", "bottom": "0px", "pointerEvents": "none"
                    }
                ),
                dcc.Interval(
                    id=ALERTS_WRAPPER_INTERVAL_ID, interval=1000, disabled=False
                ),
                html.Div(
                    id="page-content",
                    style={
                        "height": "100%", "padding": "20px", "margin": "0 auto",
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
        for page in self.views:
            if page.matches(decoded_url):
                try:
                    return page.render(decoded_params, states_for_input)
                except Exception as e:
                    traceback.print_exc()
                    return html.Div("Page under construction")

        return html.Div("404 Not Found.")
