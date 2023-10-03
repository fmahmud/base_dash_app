import datetime
import pprint
import time
from typing import List, Dict, Optional, Tuple, Union, Type

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, ALL, MATCH
from dash.exceptions import PreventUpdate
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.cards.small_card import SmallCard
from base_dash_app.components.forms.simple_selector import SimpleSelector
from base_dash_app.components.historicals import historical_dots
from base_dash_app.components.inputs.simple_labelled_input import SimpleLabelledInput
from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.services.job_definition_service import JobDefinitionService, JobDefinitionImpl
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer

SELECTABLE_ADDITIONAL_ID = "selectable_additional_id"

JOB_SELECTABLE_RUNNER_BTN_ID = "JOB_COMBO_RUNNER_BTN_ID"

JOB_CARD_TABS_ID = "JOB_CARD_TABS_ID"

JOB_CARD_LOG_LEVEL_SELECTOR_ID = "job-card-log-level-selector-id"

INDEX_DELIMITER = "||||"

JOB_CARD_PARAM_INPUT_ID = "job-card-param-input-id"

JOB_CARD_INTERVAL_ID = "job-card-interval-id"

JOB_CARD_LONG_INTERVAL_ID = "job-card-long-interval-id"

JOB_CARD_DIV_ID = "job-card-div-id"

JOB_RUNNER_BTN_ID = "job-runner-btn-id"


class JobCard(ComponentWithInternalCallback):
    def __init__(
            self, job_definition: JobDefinition,
            job_def_service: JobDefinitionService,
            footer=None,
            selectables_as_tabs=False,
            hide_log_div=False,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.job_definition: JobDefinition = job_definition
        self.job_definition_id: int = job_definition.id
        self.job_def_service: JobDefinitionService = job_def_service
        self.footer = footer or []
        self.log_level: LogLevel = LogLevelsEnum.INFO.value
        self.current_tab = 'tab-0'
        self.selectables_as_tabs = selectables_as_tabs
        self.hide_log_div = hide_log_div

        # used for each of the param combo tabs
        # used only for the custom params tab
        self.custom_prog_container: Optional[VirtualJobProgressContainer] = None
        self.any_in_progress = False

        self.selectable_param = None
        self.selectable_to_prog_containers: Dict[Selectable, Optional[VirtualJobProgressContainer]] = {}
        self.selectable_id_to_selectable: Dict[int, Selectable] = {}
        self.last_updated_at = (datetime.datetime.now() + datetime.timedelta(seconds=10)).timestamp()

    def refresh_selectables_info(self):
        """
        Refreshes the selectable_to_prog_containers dict and the selectable_id_to_selectable dict
        :return:
        """
        session: Session = self.dbm.get_session()
        in_progress_instances = self.job_definition.get_in_progress_instances_by_selectable(
            session=session,
        )
        job_class: Type[JobDefinitionImpl] = type(self.job_definition)
        self.selectable_param = self.selectable_param or type(self.job_definition).single_selectable_param_name()

        self.selectable_to_prog_containers = {
            selectable: None
            for selectable in job_class.get_selectables_by_param_name(self.selectable_param, session=session)
        }

        for ji in in_progress_instances:
            selectable: Selectable = job_class.get_selectable_for_instance(ji, session=session)
            self.selectable_to_prog_containers[selectable] = VirtualJobProgressContainer.get_from_redis_by_instance_id(
                redis_client=self.redis_client,
                ji_id=ji.id
            )

        self.selectable_id_to_selectable = {
            selectable.get_value(): selectable
            for selectable in self.selectable_to_prog_containers.keys()
        }

    @staticmethod
    def refresh_job_definition(instance: 'JobCard'):
        start_time = time.time()
        some_change = False

        if instance.last_updated_at is not None:
            for selectable, prog_container in instance.selectable_to_prog_containers.items():
                if prog_container is None or prog_container.last_status_updated_at is None:
                    continue

                if instance.last_updated_at <= prog_container.last_status_updated_at.timestamp():
                    some_change = True
                    break
        else:
            some_change = True

        if not some_change:
            instance.logger.debug(f"early exit Execution time: {time.time() - start_time} seconds")
            return

        instance.last_updated_at = time.time()
        instance.logger.debug(f"full refresh Execution time: {instance.last_updated_at - start_time} seconds")

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        # todo: parameters for job execution - look at DeployedContractView in ContractsDashboard

        instance: JobCard
        session: Session = instance.dbm.get_session()
        instance.job_definition = session.query(JobDefinition).get(instance.job_definition_id)
        job_def: JobDefinition = instance.job_definition

        instance.refresh_selectables_info()
        in_progress_containers = [i for i in instance.selectable_to_prog_containers.values() if i is not None]
        instance.logger.debug(f"num containers in progress: {len(in_progress_containers)}")

        if len(in_progress_containers) > 0:
            instance.logger.debug(f"in progress container: {pprint.pformat(in_progress_containers)}")

        callback_context = dash.callback_context
        error_messages = {}
        if triggering_id.startswith(JOB_CARD_TABS_ID):
            state_mapping = instance.get_callback_state(JOB_CARD_TABS_ID, args)
            instance.current_tab = state_mapping[JOB_CARD_TABS_ID]
        elif triggering_id.startswith(JOB_SELECTABLE_RUNNER_BTN_ID):
            instance.logger.debug(f"Running job {job_def.name} with selectable {instance.selectable_param}")
            # don't need to worry about getting parameters from different input boxes,
            # convert frozen set of tuples to dict
            if SELECTABLE_ADDITIONAL_ID not in callback_context.triggered_id:
                instance.logger.error(f"Callback Context.triggered_id does not have {SELECTABLE_ADDITIONAL_ID}")
                raise PreventUpdate

            selectable_id = int(callback_context.triggered_id[SELECTABLE_ADDITIONAL_ID])

            if selectable_id not in instance.selectable_id_to_selectable:
                instance.logger.error(
                    f"Selectable id {selectable_id} not found in instance.selectable_id_to_selectable"
                    f". Available ids: {', '.join(str(key) for key in instance.selectable_id_to_selectable.keys())}"
                )
                raise PreventUpdate

            # todo: handle JobAlreadyRunningError
            selectable = instance.selectable_id_to_selectable[selectable_id]
            instance.selectable_to_prog_containers[selectable] = (
                instance.job_def_service.run_job(
                    job_def=instance.job_definition,
                    selectable=selectable,
                    parameter_values={instance.selectable_param: selectable_id},
                    log_level=instance.log_level  # todo: fix
                )
            )

            # instance.job_definition.rehydrate_events_from_db()
            from base_dash_app.models.job_instance import JobInstance
            job_instances = (
                session.query(JobInstance)
                .filter(JobInstance.job_definition_id == instance.job_definition_id)
                .order_by(JobInstance.start_time.desc())
                .limit(30)
                .all()
            )

            instance.job_definition.clear_all()
            for job_instance in job_instances:
                instance.job_definition.process_result(job_instance.get_result(), job_instance)

        elif triggering_id.startswith(JOB_RUNNER_BTN_ID):
            """
                dash.callback_context = {
                    ...
                    "states": {...}, # don't use this...
                    "states_list": [
                        {
                            0: {
                                "id": {
                                    "index": f"{instance_id}{INDEX_DELIMITER}{param_name}", 
                                    "type": "job-card-param-input-id"
                                },
                                "property": "value",
                                "value": "<user_input>"
                            },
                            ...
                        }
                        ...                                
                    ]
                }
            """

            param_defs_dict: Dict[str, JobDefinitionParameter] = instance.job_definition.get_params_dict()
            param_to_value_map = {}
            should_run = True
            log_level: LogLevel = LogLevelsEnum.INFO.value
            for state in callback_context.states_list[0]:
                if 'id' in state and 'index' in state['id']:
                    if "index" not in state['id'] or "param_name" not in state["id"]:
                        instance.logger.error(f"Index or param_name not in state['id']: {state['id']}")
                        raise PreventUpdate

                    instance_id = state['id']['index']
                    param_name = state['id']['param_name']

                    if instance_id != instance._instance_id:
                        continue

                    param_def: JobDefinitionParameter = param_defs_dict[param_name]
                    prop = state["property"]
                    if prop not in state or state[prop] is None or state[prop] == "":
                        # no value was entered
                        if param_def.required:
                            error_messages[param_def] = "This parameter is required."
                            should_run = False
                        continue

                    try:
                        param_to_value_map[param_def.variable_name] = param_def.convert_to_correct_type(state[prop])
                    except Exception as e:
                        error_messages[param_def] = str(e)
                        should_run = False

            # convert param_to_value_map to a frozen set of tuples
            # instance.current_param_combination = frozenset(param_to_value_map.items())
            if len(callback_context.states_list) >= 2:
                # find log level at index 1
                if len(callback_context.states_list[1]) > 0:
                    # some value exists
                    log_level_state_dict = callback_context.states_list[1][0]
                    if 'id' in log_level_state_dict and 'type' in log_level_state_dict['id'] \
                        and log_level_state_dict['id']['type'] == JOB_CARD_LOG_LEVEL_SELECTOR_ID:
                        # found log level selector
                        if 'value' in log_level_state_dict and log_level_state_dict['value'] != '':
                            log_level = LogLevelsEnum.get_by_id(int(log_level_state_dict['value']))

            instance.log_level = log_level

            if should_run:
                instance.custom_prog_container = instance.job_def_service.run_job(
                    job_def=instance.job_definition, parameter_values=param_to_value_map,
                    log_level=log_level
                )

                instance.job_definition.rehydrate_events_from_db()
        elif triggering_id.startswith(JOB_CARD_INTERVAL_ID):
            # session.refresh(job_def)
            pass

        return [
            instance.__render_job_card(
                form_messages=error_messages,
                footer=instance.footer,
                dbm=instance.dbm
            )
        ]

    def render(self, wrapper_style_override=None):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        session: Session = self.dbm.get_session()
        self.job_definition = session.query(JobDefinition).get(self.job_definition_id)
        self.refresh_selectables_info()

        return html.Div(
            children=[
                self.__render_job_card(
                    footer=self.footer,
                    form_messages={},
                    dbm=self.dbm
                )
            ],
            style={
                "width": "660px", "position": "relative", "float": "left", "margin": "20px",
                **wrapper_style_override
            },
            id={"type": JobCard.get_wrapper_div_id(), "index": self._instance_id}
        )

    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_RUNNER_BTN_ID,
                    input_property="n_clicks"
                ),
                states=[
                    StateMapping(
                        state_id=JOB_CARD_PARAM_INPUT_ID,
                        state_property="value",
                        additional_key="param_name",
                        additional_value=ALL
                    ),
                    StateMapping(
                        state_id=JOB_CARD_LOG_LEVEL_SELECTOR_ID,
                        state_property="value",
                        additional_key="param_name",
                        additional_value=ALL
                    ),
                ]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_SELECTABLE_RUNNER_BTN_ID,
                    input_property="n_clicks",
                    index=MATCH,
                    additional_key=SELECTABLE_ADDITIONAL_ID,
                    additional_value=ALL
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_CARD_INTERVAL_ID,
                    input_property="n_intervals"
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_CARD_LONG_INTERVAL_ID,
                    input_property="n_intervals"
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_CARD_TABS_ID,
                    input_property="active_tab"
                ),
                states=[
                    StateMapping(
                        state_id=JOB_CARD_TABS_ID,
                        state_property="active_tab",
                    )
                ]
            )
        ]

    def __any_in_progress(self) -> Tuple[bool, bool]:
        return any([
            container.is_in_progress() for container in self.selectable_to_prog_containers.values()
            if container is not None
        ]), (
            self.custom_prog_container is not None and self.custom_prog_container.is_in_progress()
        )

    def render_log_div(self, container: VirtualJobProgressContainer, wrapper_div_style=None):
        if self.hide_log_div:
            return None

        if wrapper_div_style is None:
            wrapper_div_style = {}

        if not (container is not None and container.is_in_progress()):
            # if container doesn't exist or if it does and is not in progress, return None
            return None

        if container.logs is None:
            logs = []
        else:
            logs = container.logs

        children = []
        for log in logs:
            style = {
                "lineHeight": "18px", "margin": 0,
                "flex": "none", "color": "black", "fontWeight": "normal",
                "position": "relative", "float": "left", "overflow": "hidden"
            }

            if log.startswith("[INFO]"):
                pass
            elif log.startswith("[WARN]"):
                style["color"] = StatusesEnum.WARNING.value.hex_color
            elif log.startswith("[ERROR]"):
                style["color"] = StatusesEnum.FAILURE.value.hex_color
            elif log.startswith("[CRITICAL]"):
                style["color"] = StatusesEnum.FAILURE.value.hex_color
                style["fontWeight"] = "bold"

            children.insert(
                0, html.Pre(
                    log,
                    style=style
                )
            )

        return html.Div(
            children=children[:100],
            style={
                "width": "100%",
                "height": "100%",
                "overflow": "scroll",
                "border": "1px solid #ccc",
                "borderRadius": "5px",
                "padding": "20px",
                "display": "flex",
                "flexDirection": "column-reverse",
                "position": "relative",
                "float": "left",
                **wrapper_div_style
            },
        )

    def __render_job_card(
            self,
            dbm,
            form_messages: Dict[JobDefinitionParameter, Optional[str]] = None,
            footer=None,
    ):
        if form_messages is None:
            form_messages = {}

        if footer is None:
            footer = []

        job = self.job_definition
        session: Session = dbm.get_session()
        session.add(job)
        selectable_in_progress, custom_in_progress = self.__any_in_progress()

        last_run_error_message = None
        last_run_date = None
        if len(job.job_instances) > 0:
            job_instance = sorted(job.job_instances)[-1]
            last_run_date = job_instance.start_time

            if job_instance.result.status in [StatusesEnum.FAILURE, StatusesEnum.WARNING]:
                last_run_error_message = html.Div(
                    children=[
                        dbc.Alert(
                            job_instance.end_reason,
                            color=job_instance.result.status.value.hex_color
                        )
                    ],
                    style={"marginTop": "20px", "width": "100%", "float": "left"}
                )

        num_historical_dots = 50
        margin_right = 2
        #
        # self.logger.debug(f"__render_job_card - selectables:"
        #                  f" {', '.join(key.get_label() for key in self.selectable_to_prog_containers.keys())}")

        job_card = SmallCard(
            title=html.H3(
                children=[
                    job.name,
                    # dbc.Progress(
                    #     id=f"{self._instance_id}-progress",
                    #     value=0,
                    #     style={
                    #         # "display": "none" if self.__any_in_progress() else "block",
                    #         "height": "10px", "position": "relative", "float": "right",
                    #         "width": "200px",
                    #     },
                    #     color="success"
                    # )
                ]
            ),
            body=html.Div(
                children=[
                    html.Div(job.description) if job.description is not None else None,
                    html.Div(
                        f"Last Started {date_utils.readable_time_since(last_run_date)}"
                        f"{' ago' if last_run_date is not None else ''}"
                        if not custom_in_progress or selectable_in_progress else "In Progress",
                        style={"marginTop": "5px", "marginBottom": "5px", "fontSize": "18px", "fontWeight": "bold"}
                    ),
                    html.Div(
                        children=[
                            historical_dots.render_from_resultable_events(
                                job.events[-num_historical_dots:],
                                dot_style_override={
                                    "marginRight": f"{margin_right}px",
                                    "width": f"calc((100% - {margin_right}px "
                                             f"* {num_historical_dots}) / {num_historical_dots})",
                                    "marginLeft": "0px",
                                    "height": "26px"
                                },
                                use_tooltips=True
                            )
                        ]
                    ),
                    dcc.Interval(
                        interval=1000,
                        disabled=not (custom_in_progress or selectable_in_progress),
                        id={"type": JOB_CARD_INTERVAL_ID, "index": self._instance_id}
                    ),
                    dcc.Interval(
                        interval=30000,
                        disabled=(custom_in_progress or selectable_in_progress),
                        id={"type": JOB_CARD_LONG_INTERVAL_ID, "index": self._instance_id}
                    ),
                ]
            ),
            actions=html.Div(
                children=[
                    dbc.Label(
                        "Log Level",
                        html_for={
                            "type": JOB_CARD_LOG_LEVEL_SELECTOR_ID,
                            "index": self._instance_id
                        },
                        style={"marginTop": "20px", "position": "relative", "float": "left",
                               "clear": "left"}
                    ),
                    SimpleSelector(
                        comp_id={"type": JOB_CARD_LOG_LEVEL_SELECTOR_ID,
                                 "index": self._instance_id},
                        selectables=[level.value for level in LogLevelsEnum],
                        placeholder="Log Level",
                        style={"width": "100%", "marginBottom": "10px"},
                        disabled=custom_in_progress,
                        currently_selected_value=self.log_level.get_value()
                    ).render(),
                    html.Div(
                        children=[
                            dbc.Button(
                                "",
                                id={"type": JOB_RUNNER_BTN_ID, "index": self._instance_id},
                                style={"display": "none"}
                            ), # yet another hacky solution
                            dbc.Tabs(
                                children=[
                                    self.__render_selectable_tab(
                                        selectable=selectable,
                                        container=container,
                                    )
                                    for selectable, container in self.selectable_to_prog_containers.items()
                                ],
                                id={"type": JOB_CARD_TABS_ID, "index": self._instance_id},
                                style={
                                    "position": "relative",
                                    "float": "left",
                                    "width": "100%",
                                    "marginTop": "10px",
                                    "overflowX": "scroll",
                                    "overflowY": "hidden",
                                    "flexWrap": "nowrap",
                                },
                                active_tab=self.current_tab,
                            ) if self.selectables_as_tabs else
                            html.Div(
                                children=[
                                    self.__render_selectable_div(selectable, dbm, container)
                                    for selectable, container in sorted(
                                        [*self.selectable_to_prog_containers.items()],
                                        key=lambda s:
                                            s[1].start_time
                                            if s[1] is not None
                                            and s[1].is_in_progress()
                                            and s[1].start_time is not None
                                            else datetime.datetime.now()
                                    )
                                ] + [
                                    html.Div(
                                        "",
                                        id={"type": JOB_CARD_TABS_ID, "index": self._instance_id},
                                        style={"display": "none"}
                                    )
                                ],
                                style={"maxHeight": "800px", "overflowY": "scroll"}
                            )
                        ],
                        style={"width": "100%", "overflow": "scroll"}
                    ) if self.selectable_param is not None else
                    html.Div(
                        children=[
                            self.__render_non_selectable_tab(
                                dbm=dbm,
                                form_messages=form_messages, container=self.custom_prog_container
                            ),
                            html.Div(
                                "",
                                id={"type": JOB_CARD_TABS_ID, "index": self._instance_id},
                                style={"display": "none"}
                            )
                        ]
                    ),
                    last_run_error_message,
                    html.Div(
                        footer,
                        style={
                            "position": "relative", "float": "left", "width": "100%", "marginTop": "10px"
                        }
                    )
                ]
            )
        ).render()

        return job_card

    def __render_btn_and_prog_bar(
            self, run_btn_id: str, run_btn_index: Union[str, int],
            container: VirtualJobProgressContainer = None,
            selectable_id: int = None
    ):
        in_progress = container is not None and container.is_in_progress()
        progress = container.progress if container is not None and container.is_in_progress() else 0
        duration = date_utils.readable_time_since(
            start_time=container.start_time,
            no_negatives=True,
            short_form=True
        ) if container is not None else 0
        return html.Div(
            children=[
                dbc.Button(
                    f"{duration:.0f}s" if in_progress else "Run",
                    style={
                        "position": "relative", "float": "left", "width": "100px"
                    },
                    id={
                        "type": run_btn_id,
                        "index": run_btn_index,
                        **({SELECTABLE_ADDITIONAL_ID: str(selectable_id)} if selectable_id is not None else {})
                    },
                    disabled=in_progress
                ),
                dbc.Progress(
                    value=progress,
                    style={
                        "position": "relative", "float": "left",
                        "width": "calc(100% - 116px)", "marginLeft": "10px",
                        "marginTop": "12px"
                    },
                    label=f"{progress / 100 or 0:.1%}",
                    hide_label=not in_progress or progress is None or progress == 0
                ),
                html.Div(
                    children=self.render_log_div(
                        container=container,
                        wrapper_div_style={
                            "position": "relative", "float": "left",
                            "marginTop": "10px", "marginBottom": "10px",
                            "minHeight": "300px",
                            "maxHeight": "300px"
                        }
                    ),
                ),
            ],
            style={
                "position": "relative", "clear": "left",
                "width": "100%",
                "marginTop": "20px", "marginBottom": "20px",
                "float": "left"
            }
        )

    def __render_selectable_div(
            self, selectable: Selectable, dbm,
            container: VirtualJobProgressContainer = None
    ):
        if selectable is None:
            raise ValueError("Selectable cannot be None")

        try:
            last_exec_for_selectable = type(self.job_definition).get_latest_exec_for_selectable(
                selectable, dbm.get_session()
            )
        except InvalidRequestError as ire:
            self.logger.error(f"InvalidRequestError: {ire}")
            last_exec_for_selectable = type(self.job_definition).get_latest_exec_for_selectable(
                selectable, dbm.get_session()
            )

        last_run_time = last_exec_for_selectable.start_time if last_exec_for_selectable is not None else None
        next_run_time = (datetime.timedelta(seconds=self.job_definition.seconds_between_runs)
                         + last_run_time) if last_run_time is not None else datetime.datetime.now()

        if next_run_time is not None and next_run_time < datetime.datetime.now():
            next_run_time = datetime.datetime.now()

        return html.Div(
            children=[
                selectable.get_label_div(),
                html.Div(f"Last Ran {date_utils.readable_time_since(last_run_time)} ago"),
                html.Div(
                    f"Next run in {date_utils.readable_time_since(next_run_time)}"
                ) if self.job_definition.repeats else None,
                self.__render_btn_and_prog_bar(
                    run_btn_id=JOB_SELECTABLE_RUNNER_BTN_ID,
                    run_btn_index=self._instance_id,
                    container=container,
                    selectable_id=selectable.get_value()
                )
            ],
            style={
                "position": "relative", "float": "left", "clear": "left",
                "width": "100%", "marginTop": "10px"
            }
        )

    def __render_selectable_tab(self, selectable: Selectable, container: VirtualJobProgressContainer = None):
        if selectable is None:
            raise ValueError("Selectable cannot be None")

        return dbc.Tab(
            label=selectable.get_label(),
            label_style={
                "animation": "blinker_animation 0.6s cubic-bezier(1, 0, 0, 1) infinite alternate",
            } if container is not None and container.is_in_progress() else {},
            children=[
                self.__render_btn_and_prog_bar(
                    run_btn_id=JOB_SELECTABLE_RUNNER_BTN_ID,
                    run_btn_index=self._instance_id,
                    container=container,
                    selectable_id=selectable.get_value()
                )
            ]
        )

    def __render_non_selectable_tab(
            self, dbm,
            form_messages: Dict[JobDefinitionParameter, str] = None,
            container: VirtualJobProgressContainer = None
    ):
        if form_messages is None:
            form_messages = {}

        session: Session = dbm.get_session()

        custom_in_progress = container is not None and container.is_in_progress()
        job: JobDefinition = self.job_definition

        parameter_defs: List[JobDefinitionParameter] = job.parameters
        rendered_params = []
        for param in parameter_defs:
            if param.param_type in [int, float, str]:
                rendered_params.append(
                    SimpleLabelledInput(
                        label=param.user_facing_param_name,
                        input_id={
                            "type": JOB_CARD_PARAM_INPUT_ID,
                            "index": self._instance_id,  # f"{self._instance_id}{INDEX_DELIMITER}{param.variable_name}",
                            "param_name": param.variable_name
                        },
                        input_type="number" if param.param_type in [int, float] else "text",
                        placeholder=param.placeholder,
                        initial_validity=None if param not in form_messages else False,
                        invalid_form_feedback=form_messages[param] if param in form_messages else None,
                        disabled=param.editable is False or custom_in_progress,
                        starting_value=param.default_value,
                        style_override={"marginBottom": "20px"}
                    ).render(wrapper_style_override={"marginTop": "0px"})
                )
            elif param.param_type in [bool, Selectable]:
                if param.param_type == Selectable:
                    selectables = job.get_selectables_by_param_name(
                        param.variable_name,
                        session=session
                    )
                else:
                    selectables = [
                        CachedSelectable(label="True", value=True),
                        CachedSelectable(label="False", value=False),
                    ]

                comp_id = {
                    "type": JOB_CARD_PARAM_INPUT_ID,
                    "index": self._instance_id,  # f"{self._instance_id}{INDEX_DELIMITER}{param.variable_name}"
                    "param_name": param.variable_name
                }

                if param.user_facing_param_name is not None:
                    rendered_params.append(dbc.Label(param.user_facing_param_name, html_for=comp_id))

                rendered_params.append(
                    SimpleSelector(
                        comp_id=comp_id,
                        selectables=selectables,
                        placeholder=param.placeholder,
                        style={
                            "width": "100%", "marginBottom": "20px", "padding": "10px"
                        },
                        disabled=param.editable is False or custom_in_progress,
                    ).render(),
                )

        return dbc.Tab(
            label="Custom Params",
            children=[
                self.__render_btn_and_prog_bar(
                    run_btn_id=JOB_RUNNER_BTN_ID,
                    run_btn_index=self._instance_id,
                    container=self.custom_prog_container
                ),
                html.Div(
                    children=rendered_params,
                    style={
                        "width": "100%", "position": "relative", "float": "left",
                        "marginBottom": "10px"
                    }
                ) if len(rendered_params) > 0 and not custom_in_progress else None,
            ]
        )
