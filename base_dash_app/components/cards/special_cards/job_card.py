import datetime
from typing import List, Type, Dict, Tuple, Optional

import dash
from dash import html, dcc, ALL
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session

from base_dash_app.components.base_component import BaseComponent, ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.cards.small_card import SmallCard
from base_dash_app.components.historicals import historical_dots
from base_dash_app.components.inputs.SimpleLabelledInput import SimpleLabelledInput
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.virtual_objects.interfaces.resultable_event import CachedResultableEvent
import dash_bootstrap_components as dbc

from base_dash_app.virtual_objects.job_parameter import JobParameterDefinition
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer

INDEX_DELIMITER = "||||"

JOB_CARD_PARAM_INPUT_ID = "job-card-param-input-id"

JOB_CARD_INTERVAL_ID = "job-card-interval-id"

JOB_CARD_DIV_ID = "job-card-div-id"

JOB_RUNNER_BTN_ID = "job-runner-btn-id"


class JobCard(ComponentWithInternalCallback):
    def __init__(self, job_definition: JobDefinition, job_def_service: JobDefinitionService, *args, **kwargs):
        super().__init__()
        self.job_definition: JobDefinition = job_definition
        self.job_def_service: JobDefinitionService = job_def_service

    @classmethod
    def validate_state_on_trigger(cls, instance):
        if type(instance) != cls:
            raise PreventUpdate(f"Instance was of type {type(instance)} instead of {cls}")

        return

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

            print("JobCard: running job!")

            param_defs_dict: Dict[str, JobParameterDefinition] = instance.job_definition.get_params_dict()
            param_to_value_map = {}
            should_run = True
            for state in callback_context.states_list[0]:
                if 'id' in state and 'index' in state['id']:
                    instance_id, param_name = tuple(state['id']['index'].split(INDEX_DELIMITER))
                    if int(instance_id) != instance._instance_id:
                        continue

                    param_def: JobParameterDefinition = param_defs_dict[param_name]
                    prop = state["property"]
                    if prop not in state:
                        # no value was entered
                        if param_def.required:
                            error_messages[param_def] = "This parameter is required."
                            should_run = False
                        continue

                    param_to_value_map[param_name] = param_def.convert_to_correct_type(state[prop])

            if should_run:
                instance.progress_container = instance.job_def_service.run_job(
                    job_def=instance.job_definition, **param_to_value_map
                )

        return [instance.__render_job_card(form_messages=error_messages)]

    def render(self, *args, **kwargs):
        return html.Div(
            children=[
                self.__render_job_card()
            ],
            style={"maxWidth": "660px", "padding": "12px"},
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
                    )
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

    def __render_job_card(self, form_messages: Dict[JobParameterDefinition, Optional[str]] = None):
        if form_messages is None:
            form_messages = {}

        job: JobDefinition = self.job_definition
        is_in_progress = job.current_prog_container is not None

        job_class: Type[JobDefinition] = type(job)
        if job_class == JobDefinition:
            raise Exception("Trying to render JobDefinition instead of child class.")

        last_run_error_message = None

        if len(job.job_instances) > 0:
            job_instance = sorted(job.job_instances)[-1]
            last_run_date = job_instance.start_time
            difference = datetime.datetime.now() - last_run_date
            difference_in_days = f"{difference / datetime.timedelta(days=1):.1f} day(s) ago"

            if job_instance.result.status != StatusesEnum.SUCCESS:
                last_run_error_message = html.Div(
                    children=[
                        dbc.Alert(
                            job_instance.end_reason,
                            color=job_instance.result.status.value.hex_color
                        )
                    ],
                    style={"marginTop": "20px", "marginLeft": "10px", "width": "calc(100% - 20px)", "float": "left"}
                )
        else:
            difference_in_days = "N/A"

        parameter_defs: List[JobParameterDefinition] = job_class.get_parameters()
        rendered_params = []
        for param in parameter_defs:
            rendered_params.append(
                SimpleLabelledInput(
                    input_id={
                        "type": JOB_CARD_PARAM_INPUT_ID,
                        "index": f"{self._instance_id}{INDEX_DELIMITER}{param.param_name}"
                    },
                    input_type="number" if param.param_type in [int, float] else "text",
                    placeholder=param.param_name,
                    initial_validity=None if param not in form_messages else False,
                    invalid_form_feedback=form_messages[param] if param in form_messages else None,
                ).render()
            )

        progress = job.current_prog_container.progress if is_in_progress else 0
        job_card = SmallCard(
            title=html.H3(job.name),
            body=html.Div(
                children=[
                    html.Div(f"Last Run: {difference_in_days}" if not is_in_progress else "In Progress"),
                    html.Div(
                        children=[
                            historical_dots.render_from_resultable_events(
                                job.events[-10:],
                                dot_style_override={"borderRadius": "0px", "marginRight": "4px", "width": "45px"},
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
                                "Running..." if is_in_progress else "Run",
                                style={"position": "relative", "float": "left", "width": "100px"},
                                id={"type": JOB_RUNNER_BTN_ID, "index": self._instance_id},
                                disabled=is_in_progress
                            ),
                            dbc.Progress(
                                value=progress,
                                style={
                                    "position": "relative", "float": "left",
                                    "width": "calc(100% - 120px)", "margin": "10px"
                                }
                            ),
                            dcc.Interval(
                                interval=1000,
                                disabled=not is_in_progress,
                                id={"type": JOB_CARD_INTERVAL_ID, "index": self._instance_id}
                            ),
                            html.Div(
                                children=rendered_params,
                                style={"width": "100%", "position": "relative", "float": "left", "marginTop": "10px"}
                            ) if len(rendered_params) > 0 else None
                        ],
                        style={
                            "position": "relative", "float": "left",
                            "width": "100%", "padding": "10px"
                        }
                    ),
                ],
            ),
        ).render()

        print("Job is in progress: " + str(job.is_in_progress()))
        print(f"Job Progress = {job.get_progress()}")

        return job_card
