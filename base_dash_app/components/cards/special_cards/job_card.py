import datetime
from typing import List, Type, Dict, Optional

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, ALL
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.cards.small_card import SmallCard
from base_dash_app.components.forms.simple_selector import SimpleSelector
from base_dash_app.components.historicals import historical_dots
from base_dash_app.components.inputs.simple_labelled_input import SimpleLabelledInput
from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable

JOB_CARD_LOG_LEVEL_SELECTOR_ID = "job-card-log-level-selector-id"

INDEX_DELIMITER = "||||"

JOB_CARD_PARAM_INPUT_ID = "job-card-param-input-id"

JOB_CARD_INTERVAL_ID = "job-card-interval-id"

JOB_CARD_DIV_ID = "job-card-div-id"

JOB_RUNNER_BTN_ID = "job-runner-btn-id"


class JobCard(ComponentWithInternalCallback):
    def __init__(
            self, job_definition: JobDefinition,
            job_def_service: JobDefinitionService,
            footer=None,
            *args, **kwargs
    ):
        super().__init__()
        self.job_definition: JobDefinition = job_definition
        self.job_def_service: JobDefinitionService = job_def_service
        self.footer = footer or []
        self.log_level: LogLevel = LogLevelsEnum.INFO.value

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        # todo: parameters for job execution - look at DeployedContractView in ContractsDashboard

        instance: JobCard
        job_def: JobDefinition = instance.job_definition
        session: Session = Session.object_session(job_def)
        session.refresh(job_def)

        callback_context = dash.callback_context
        error_messages = {}
        if triggering_id.startswith(JOB_RUNNER_BTN_ID):
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
                    instance_id, param_name = tuple(state['id']['index'].split(INDEX_DELIMITER))
                    if int(instance_id) != instance._instance_id:
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
                instance.progress_container = instance.job_def_service.run_job(
                    job_def=instance.job_definition, parameter_values=param_to_value_map,
                    log_level=log_level
                )

                instance.job_definition.rehydrate_events_from_db()

        return [instance.__render_job_card(form_messages=error_messages, footer=instance.footer)]

    def render(self, wrapper_style_override=None):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        return html.Div(
            children=[
                self.__render_job_card(footer=self.footer)
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
                        index=ALL
                    ),
                    StateMapping(
                        state_id=JOB_CARD_LOG_LEVEL_SELECTOR_ID,
                        state_property="value",
                        index=ALL
                    ),
                ]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=JOB_CARD_INTERVAL_ID,
                    input_property="n_intervals"
                ),
                states=[]
            )
        ]

    def render_log_div(self, wrapper_div_style=None):
        if wrapper_div_style is None:
            wrapper_div_style = {}

        if not self.job_definition.is_in_progress():
            return None

        logs = self.job_definition.current_prog_container.logs

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
            self, form_messages: Dict[JobDefinitionParameter, Optional[str]] = None,
            footer=None
    ):
        if form_messages is None:
            form_messages = {}

        if footer is None:
            footer = []

        job = self.job_definition
        is_in_progress = job.current_prog_container is not None

        last_run_error_message = None

        if len(job.job_instances) > 0:
            job_instance = sorted(job.job_instances)[-1]
            last_run_date = job_instance.start_time
            difference = datetime.datetime.now() - last_run_date
            difference_in_days = f"{difference / datetime.timedelta(days=1):.1f} day(s) ago"

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
        else:
            difference_in_days = "N/A"

        parameter_defs: List[JobDefinitionParameter] = job.parameters
        rendered_params = []
        for param in parameter_defs:
            if param.param_type in [int, float, str]:
                rendered_params.append(
                    SimpleLabelledInput(
                        label=param.user_facing_param_name,
                        input_id={
                            "type": JOB_CARD_PARAM_INPUT_ID,
                            "index": f"{self._instance_id}{INDEX_DELIMITER}{param.variable_name}"
                        },
                        input_type="number" if param.param_type in [int, float] else "text",
                        placeholder=param.placeholder,
                        initial_validity=None if param not in form_messages else False,
                        invalid_form_feedback=form_messages[param] if param in form_messages else None,
                        disabled=param.editable is False or is_in_progress,
                        starting_value=param.default_value,
                        style_override={"marginBottom": "20px"}
                    ).render(wrapper_style_override={"marginTop": "0px"})
                )
            elif param.param_type in [bool, Selectable]:
                if param.param_type == Selectable:
                    selectables = job.get_cached_selectables_by_param_name(
                        param.variable_name,
                        session=self.job_def_service.dbm.get_session()
                    )
                else:
                    selectables = [
                        CachedSelectable(label="True", value=True),
                        CachedSelectable(label="False", value=False),
                    ]

                comp_id = {
                    "type": JOB_CARD_PARAM_INPUT_ID,
                    "index": f"{self._instance_id}{INDEX_DELIMITER}{param.variable_name}"
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
                        disabled=param.editable is False or is_in_progress,
                    ).render(),
                )

        num_historical_dots = 15
        margin_right = 4
        progress = job.current_prog_container.progress if is_in_progress else 0
        job_card = SmallCard(
            title=html.H3(job.name),
            body=html.Div(
                children=[
                    html.Div(job.description) if job.description is not None else None,
                    html.Div(f"Last Run: {difference_in_days}" if not is_in_progress else "In Progress"),
                    html.Div(
                        children=[
                            historical_dots.render_from_resultable_events(
                                job.events[-num_historical_dots:],
                                dot_style_override={
                                    "marginRight": f"{margin_right}px",
                                    "width": f"calc((100% - {margin_right}px "
                                             f"* {num_historical_dots}) / {num_historical_dots})",
                                    "marginLeft": "0px"
                                },
                                use_tooltips=True
                            )
                        ]
                    ),
                ]
            ),
            actions=html.Div(
                children=[
                    html.Div(
                        children=[
                            dbc.Button(
                                f"{job.get_current_duration()}s" if is_in_progress else "Run",
                                style={
                                    "position": "relative", "float": "left", "width": "100px"
                                },
                                id={"type": JOB_RUNNER_BTN_ID, "index": self._instance_id},
                                disabled=is_in_progress
                            ),
                            dbc.Progress(
                                value=progress,
                                style={
                                    "position": "relative", "float": "left",
                                    "width": "calc(100% - 116px)", "marginLeft": "10px",
                                    "marginTop": "10px"
                                },
                                label=f"{(progress / 100) or 0:.1%}",
                                hide_label=not is_in_progress or progress is None or progress == 0
                            ),
                            dcc.Interval(
                                interval=1000,
                                disabled=not is_in_progress,
                                id={"type": JOB_CARD_INTERVAL_ID, "index": self._instance_id}
                            ),
                            dbc.Label(
                                "Log Level",
                                html_for={"type": JOB_CARD_LOG_LEVEL_SELECTOR_ID, "index": self._instance_id},
                                style={"marginTop": "20px", "position": "relative", "float": "left", "clear": "left"}
                            ),
                            SimpleSelector(
                                comp_id={"type": JOB_CARD_LOG_LEVEL_SELECTOR_ID, "index": self._instance_id},
                                selectables=[level.value for level in LogLevelsEnum],
                                placeholder="Log Level",
                                style={"width": "100%", "marginBottom": "10px"},
                                disabled=is_in_progress,
                                currently_selected_value=self.log_level.get_value()
                            ).render(),
                            last_run_error_message,
                            html.Div(
                                children=rendered_params,
                                style={
                                    "width": "100%", "position": "relative", "float": "left", "marginBottom": "10px"
                                }
                            ) if len(rendered_params) > 0 and not is_in_progress else None,
                            html.Div(
                                children=self.render_log_div(
                                    wrapper_div_style={
                                        "minHeight": "300px",
                                        "maxHeight": "300px"
                                    }
                                ),
                            ),
                            html.Div(
                                children=footer,
                                style={
                                    "width": "100%", "position": "relative", "float": "left", "marginBottom": "10px"
                                }
                            ) if footer is not None else None
                        ],
                        style={
                            "position": "relative", "clear": "left",
                            "width": "100%", "padding": "10px"
                        }
                    ),
                ],
            ),
        ).render()

        return job_card
