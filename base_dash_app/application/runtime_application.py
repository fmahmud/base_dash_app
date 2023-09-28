import datetime
import logging
import os
import threading
import traceback
from operator import itemgetter
from typing import List, Callable, Dict, Type, Union, TypeVar, Any, Optional
from urllib.parse import unquote

import dash
import dash_auth
import psutil
import redis
import sqlalchemy.exc
from apscheduler.schedulers.background import BackgroundScheduler
from celery import Celery
from celery.schedules import crontab
from dash import dcc, html
from dash.dependencies import Output, Input, State, ALL
from dash.exceptions import PreventUpdate
from pympler import tracker
from redis import Redis
from sqlalchemy.orm import Session

from base_dash_app.apis.api import API
from base_dash_app.application.app_descriptor import AppDescriptor
from base_dash_app.application.db_declaration import db
from base_dash_app.components import alerts
from base_dash_app.components.alerts import Alert
from base_dash_app.components.async_task_controls import AsyncTaskControls
from base_dash_app.components.callback_utils.mappers import InputToState
from base_dash_app.components.callback_utils.utils import get_triggering_id_from_callback_context, \
    get_state_values_for_input_from_args_list, invalid_n_clicks
from base_dash_app.components.cards.special_cards.job_card import JobCard
from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpSparklineStatCard
from base_dash_app.components.celery_task_controls import CeleryTaskControls
from base_dash_app.components.dashboards.simple_timeseries_dashboard import SimpleTimeSeriesDashboard
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.components.navbar import NavBar, NavDefinition, NavGroup
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.async_handler_service import AsyncHandlerService
from base_dash_app.services.base_service import BaseService
from base_dash_app.services.celery_handler_service import CeleryHandlerService
from base_dash_app.services.global_state_service import GlobalStateService
from base_dash_app.services.job_definition_service import JobDefinitionService, JobAlreadyRunningException
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.utils.env_vars.env_var_def import EnvVarDefinition
from base_dash_app.views.admin_statistics_dash import AdminStatisticsDash
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.interfaces.selectable import Selectable
from base_dash_app.virtual_objects.interfaces.startable import Startable, ExternalTriggerEvent
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.virtual_objects.timeseries.time_series import TimeSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject

ALERTS_WRAPPER_INTERVAL_ID = "alerts-wrapper-interval-id"

ALERTS_WRAPPER_DIV_ID = "alerts-wrapper-div-id"


class RuntimeApplication:
    _instance = None
    _pid_to_dbm_map: Dict[int, DbManager] = {}

    @classmethod
    def get_instance(cls) -> "RuntimeApplication":
        if cls._instance is None:
            raise Exception("RuntimeApplication is not initialized.")
        return cls._instance

    def get_dbm_by_pid(self) -> DbManager:
        pid = os.getpid()
        if pid not in RuntimeApplication._pid_to_dbm_map:
            RuntimeApplication._pid_to_dbm_map[pid] = DbManager(self.app_descriptor.db_descriptor, self.server)

        return RuntimeApplication._pid_to_dbm_map[pid]

    def __init__(self, app_descriptor: AppDescriptor):
        # will not be used if running in gunicorn or celery
        self.bg_scheduler: Optional[BackgroundScheduler] = None
        if RuntimeApplication._instance is not None:
            return

        RuntimeApplication._instance = self

        self.last_job_check = None
        self.app_descriptor: AppDescriptor = app_descriptor

        from base_dash_app.utils.logger_utils import configure_logging
        configure_logging(
            logging_format=app_descriptor.logging_format,
            log_level=app_descriptor.log_level,
            std_out_formatter=app_descriptor.std_out_formatter
        )

        self.app = dash.Dash(
            title=app_descriptor.title,
            external_stylesheets=app_descriptor.external_stylesheets,
            suppress_callback_exceptions=True,
            assets_folder=app_descriptor.assets_folder_path or "assets",
            update_title=None
        )

        #issue: (issue: 188): Add validation for health endpoint path provided
        @self.app.server.route(self.app_descriptor.health_endpoint_path, methods=['GET'])
        def health():
            return "OK", 200

        self.app.logger.handlers.clear()
        self.app.logger.setLevel(app_descriptor.log_level or logging.INFO)

        if app_descriptor.use_auth:
            self.auth = dash_auth.BasicAuth(
                self.app,
                app_descriptor.valid_user_pairs
            )

        self.server = self.app.server
        self.redis_client: Redis = redis.StrictRedis(
            host=os.getenv("REDIS_HOST", "redis"), port=6379, db=1,
            decode_responses=True
        )

        try:
            if self.redis_client.ping():
                self.app.logger.debug("Connected to Redis.")
        except redis.exceptions.ConnectionError:
            self.app.logger.error("Could not connect to Redis.")

        # need to set celery instance from outside, so it can be referenced when decorating tasks
        self.celery: Optional[Celery] = None

        self.dbm = None

        self.active_alerts: List[Alert] = []
        self.services: Dict[Type, BaseService] = {}
        self.apis: Dict[Type, API] = {}
        self.views: Dict[Type, BaseView] = {}
        self.env_vars: Dict[str, EnvVarDefinition] = {}
        self.jobs: Dict[Type, JobDefinition] = {}
        for e in self.app_descriptor.env_vars:
            e.value = e.var_type(os.getenv(e.name))
            if e.value is None or e.value == "None" and e.required:
                raise Exception(f"Could not find required environment variable: {e.name}.")

            self.env_vars[e.name] = e

        def push_new_alert(alert: Alert):
            if type(alert) != Alert:
                raise Exception(f"Trying to push alert of incorrect type: {type(alert)}.")
            self.active_alerts.append(alert)

        def remove_alert(alert: Alert):
            if alert is not None and alert in self.active_alerts:
                self.active_alerts.remove(alert)

        Service = TypeVar("Service", bound=BaseService)

        def get_service_by_type(service_class: Type) -> Service:
            return self.services.get(service_class)

        def get_api_by_type(api_class: Type) -> API:
            return self.apis.get(api_class)

        def get_all_apis() -> Dict[Type, API]:
            return self.apis

        def get_job_by_class(clazz):
            return self.jobs[clazz]

        def get_view_by_type(view_class: Type) -> BaseView:
            return self.views.get(view_class)

        # with self.app.server.app_context():
        if app_descriptor.db_descriptor is not None:
            self.dbm = DbManager(
                app_descriptor.db_descriptor,
                app=self.app.server,
            )

        with self.dbm as dbm:
            if self.dbm is not None and app_descriptor.upgrade_db:
                self.dbm.upgrade_db(drop_first=app_descriptor.drop_tables)

            self.last_mem_check = datetime.datetime(1970, 1, 1)
            self.memory_history_timeseries: TimeSeries = TimeSeries(
                title="Memory History",
                unique_id="memory_history",
            )

            self.cpu_history_timeseries: TimeSeries = TimeSeries(
                title="CPU History",
                unique_id="cpu_history",
            )

            self.base_service_args = base_service_args = {
                "dbm": self.dbm,
                "service_provider": get_service_by_type,
                "api_provider": get_api_by_type,
                "all_apis": get_all_apis,
                "register_callback_func": self.register_callback,
                "push_alert": push_new_alert,
                "remove_alert": remove_alert,
                "env_vars": self.env_vars,
                "job_provider": get_job_by_class,
                "view_provider": get_view_by_type,
                "redis_client": self.redis_client
            }

            for api_type in app_descriptor.apis:
                self.apis[api_type] = api_type(**base_service_args)  # parent constructor vars will come from child

            session: Session = self.dbm.get_session()
            job_def_service: JobDefinitionService = JobDefinitionService(**base_service_args)
            all_jobs_from_db: List[JobDefinition] = job_def_service.get_all(session)
            all_job_classes = set([type(jd) for jd in all_jobs_from_db])

            required_job_to_class_map = {job_type.__name__: job_type for job_type in app_descriptor.jobs}

            for class_name, job_class in required_job_to_class_map.items():
                if issubclass(job_class, JobDefinition) and job_class.autoinitialize():
                    if job_class not in all_job_classes:
                        # job was never saved to DB and it should be autoinitialized
                        job = job_class.construct_instance(**base_service_args)
                        job_def_service.save(job, session=session)

                        all_jobs_from_db.append(job)
                        all_job_classes.add(job_class)
                    elif job_class.force_update():
                        #issue: (issue: 176): properly handle JobDefinitions when force update is True - or remove functionality
                        pass

            for s in app_descriptor.service_classes:
                self.services[s] = s(**base_service_args)

            self.services[GlobalStateService] = GlobalStateService(initial_state=app_descriptor.initial_global_state)
            self.services[JobDefinitionService] = job_def_service
            self.services[AsyncHandlerService] = AsyncHandlerService(
                **base_service_args,
                max_workers=app_descriptor.max_num_threads
            )
            self.services[CeleryHandlerService] = CeleryHandlerService(**base_service_args)

            base_view_args = base_service_args

            for view in app_descriptor.views:
                self.views[view] = view(**base_view_args)

            self.views[AdminStatisticsDash] = AdminStatisticsDash(
                memory_timeseries=self.memory_history_timeseries,
                cpu_timeseries=self.cpu_history_timeseries,
                **base_view_args
            )

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
                output=[
                    Output(ALERTS_WRAPPER_DIV_ID, "children"),
                    Output("nav-bar-memory-consumption-bar", "value"),
                    Output("nav-bar-memory-consumption-label", "children"),
                    Output("nav-bar-cpu-usage-bar", "value"),
                    Output("nav-bar-cpu-usage-label", "children"),
                ],
                inputs=[
                    Input({"type": alerts.DISMISS_ALERT_BTN_ID, "index": ALL}, "n_clicks"),
                    Input(ALERTS_WRAPPER_INTERVAL_ID, "n_intervals"),
                    Input(alerts.CLEAR_ALL_ALERTS_BTN_ID, "n_clicks"),
                ],
                state=[],
                function=self.bind_to_self(self.handle_alerts)
            )

            # register internal callback components
            components_with_internal_callbacks = [
                JobCard, DataTableWrapper, SimpleTimeSeriesDashboard, TsdpSparklineStatCard,
                AsyncTaskControls, CeleryTaskControls,
                *app_descriptor.components_with_internal_callbacks
            ]

            for comp_class in components_with_internal_callbacks:
                comp_class.do_registrations(self.register_callback)

            self.navbar = self.initialize_navbar(
                app_descriptor.extra_nav_bar_components, app_descriptor.view_groups
            )

            self.app.layout = self.get_layout

    def handle_alerts(self, n_clicks, n_interval, clear_all_nclicks, *args, **kwargs):
        if invalid_n_clicks(n_clicks) and invalid_n_clicks(n_interval) \
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

        for alert in self.active_alerts:
            if alert.duration is not None and alert.created_at is not None \
                    and alert.created_at + datetime.timedelta(seconds=alert.duration) <= datetime.datetime.now():
                self.active_alerts.remove(alert)

        if self.last_mem_check < datetime.datetime.now() - datetime.timedelta(seconds=60):
            if self.app_descriptor.disable_memory_capture:
                pass
            else:
                self.track_memory_usage()

        # issue: (issue: 187): Store memory and CPU usage timeseries in redis with PIDs as keys
        latest_memory = self.memory_history_timeseries[-1].value if len(self.memory_history_timeseries) > 0 else 0
        latest_cpu = self.cpu_history_timeseries[-1].value if len(self.cpu_history_timeseries) > 0 else 0

        return [
            alerts.render_alerts_div(self.active_alerts),
            latest_memory,
            f"{latest_memory:.1f} MB",
            latest_cpu,
            f"{latest_cpu:.1f}%"
        ]

    def track_memory_usage(self):
        self.app.logger.info("Capturing memory usage")
        self.last_mem_check = datetime.datetime.now()

        mem = tracker.SummaryTracker()
        memory_usages = list(sorted(mem.create_summary(), reverse=True, key=itemgetter(2)))
        self.memory_history_timeseries.add_tsdp(
            TimeSeriesDataPoint(
                date=datetime.datetime.now(),
                value=sum([mu[2] for mu in memory_usages]) / (1024 ** 2)
            )
        )

        self.cpu_history_timeseries.add_tsdp(
            TimeSeriesDataPoint(
                date=datetime.datetime.now(),
                value=psutil.cpu_percent()
            )
        )

    def check_for_scheduled_jobs(self):
        self.app.logger.debug("Checking for scheduled jobs")
        self.last_job_check = datetime.datetime.now()
        # print current process and thread ids
        self.app.logger.debug(f"Current process id: {os.getpid()}")
        self.app.logger.debug(f"Current thread id: {threading.current_thread().ident}")

        with self.dbm as dbm:
            session: Session = dbm.get_session()
            job_def_service: JobDefinitionService = self.base_service_args["service_provider"](JobDefinitionService)
            try:
                jobs: List[JobDefinition] = job_def_service.get_all(session=session)
                self.app.logger.debug(f"Checking {len(jobs)} jobs for scheduled runs.")
                for job in jobs:
                    self.app.logger.debug(f"Checking job {job.name}")

                    job: JobDefinition
                    job_class = type(job)
                    job.set_vars_from_kwargs(**self.base_service_args)
                    selectable_param_name = job.single_selectable_param_name
                    selectables: List[Selectable] = job_class.get_selectables_by_param_name(
                        job_class.single_selectable_param_name(),
                        session=session
                    )
                    for selectable in selectables:
                        latest_instance: JobInstance = job.get_latest_exec_for_selectable(selectable, session)

                        self.app.logger.info(
                            f"job.repeats: {job.repeats}, "
                            f"latest_instance is None: {latest_instance is None}, "
                            f"seconds_between_runs: {job.seconds_between_runs}, "
                            f"selectable value: {selectable.get_value()}, "
                        )

                        if not job.repeats:
                            continue

                        if latest_instance is not None and latest_instance.end_time is None:
                            # job still in progress
                            self.app.logger.info(f"Job {job.name} is still in progress.")
                            continue

                        last_start_time = (
                            latest_instance.start_time
                            if latest_instance is not None else datetime.datetime(1970, 1, 1)
                        )

                        next_start_time = last_start_time + datetime.timedelta(seconds=job.seconds_between_runs)

                        self.app.logger.info(
                            f"Checking job {job.name} with {selectable_param_name} = {selectable.get_label()}:"
                            f"last_start_time: {last_start_time}, "
                            f"next_start_time: {next_start_time}"
                        )

                        if next_start_time <= datetime.datetime.now():
                            self.app.logger.info(
                                f"Running job {job.name} with {selectable_param_name} = {selectable.get_label()}"
                            )
                            try:
                                job_def_service.run_job(
                                    job_def=job,
                                    selectable=selectable,
                                    parameters={selectable_param_name: selectable.get_value()}
                                )

                                self.base_service_args["push_alert"](
                                    Alert(
                                        f"Running job {job.name} "
                                        f"with {selectable_param_name} = {selectable.get_label()}",
                                        duration=15,
                                        color="success"
                                    )
                                )

                                # return
                            except JobAlreadyRunningException as jare:
                                self.app.logger.warning(
                                    f"Job {job.name} with {selectable_param_name} = {selectable.get_label()} is already running"
                                )
                            except Exception as inner_e:
                                stack_trace = traceback.format_exc()
                                self.app.logger.error(
                                    f"Error while running job {job.name} "
                                    f"with {selectable_param_name} = {selectable.get_label()}: {inner_e}\n{stack_trace}"
                                )
            except Exception as e:
                stack_trace = traceback.format_exc()
                self.app.logger.error(f"Error while checking for scheduled jobs: {e}\n{stack_trace}")
                session.rollback()
            finally:
                session.close()

    def run_server(self, **kwargs):
        """
        this no longer does anything - deprecated
        :param kwargs:
        :return:
        """
        pass

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

        for page in self.views.values():
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
                        "zIndex": "10000", "position": "absolute", "right": "0", "top": "71px",
                        "width": "580px", "bottom": "0px", "pointerEvents": "none"
                    }
                ),
                dcc.Interval(
                    id=ALERTS_WRAPPER_INTERVAL_ID,
                    interval=self.app_descriptor.alerts_refresh_timeout or 1000,
                    disabled=False
                ),
                html.Div(
                    id="page-content",
                    style={
                        "padding": "20px", "margin": "0 auto",
                        "position": "relative", "float": "left",
                        "minWidth": "100vw", "maxWidth": "100vw",
                        "minHeight": "calc(100vh - 71px)",
                        "maxHeight": "calc(100vh - 71px)",
                        "overflow": "scroll"
                    }
                ),
            ],
            style={"fontFamily": "'Roboto', sans-serif"}
        )

    def register_callback(
            self, output: Union[Output, List[Output]], inputs: List[Input], state: List[State],
            function: Callable, prevent_initial_call: bool = True
    ):
        self.app.callback(
            output=output,
            inputs=inputs,
            state=state,
            prevent_initial_call=prevent_initial_call
        )(function)

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
        for page in self.views.values():
            if page.matches(decoded_url):
                try:
                    return page.render(decoded_params, states_for_input)
                except sqlalchemy.exc.SQLAlchemyError:
                    #issue: (issue: 177): Try reproducing this error and remove if not possible
                    exception_trace = traceback.format_exc()
                    self.app.logger.error(exception_trace)
                    self.dbm.get_session().rollback()
                    return self.handle_get_call(url, query_params, *args)
                except Exception:
                    exception_trace = traceback.format_exc()
                    self.app.logger.error(exception_trace)
                    return html.Pre(exception_trace, style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"})

        return html.Div("404 Not Found.")
