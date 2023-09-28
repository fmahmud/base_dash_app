import json
import pprint
from typing import Optional, Callable, Dict, Any

from dash import html, dcc
import dash_bootstrap_components as dbc

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.datatable.download_and_reload_bg import construct_down_ref_btgrp
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.async_vos.celery_task import CeleryTask, CeleryOrderedTaskGroup

CELERY_CONTROLS_EXPAND_BTN_ID = "CELERY_CONTROLS_EXPAND_BTN_ID"

RELOAD_CELERY_TASK_BTN_ID = "RELOAD_CELERY_TASK_BTN_ID"

CELERY_TASK_DOWNLOAD_CONTENT_ID = "CELERY_TASK_DOWNLOAD_CONTENT_ID"

CELERY_TASK_DOWNLOAD_BTN_ID = "download-celery-task-controls-btn-id"

CELERY_TASK_INTERVAL_ID = "celery-task-interval-id"


class CeleryTaskControls(ComponentWithInternalCallback):
    def __init__(
            self,
            celery_task: CeleryTask,
            extra_text=None,
            show_download_button=True,
            collapsable=True,
            interval_duration=1000,
            render_interval=True,
            download_formatter_func=lambda x: json.dumps(x),
            download_file_format="json",
            extra_buttons=None,
            get_kwargs_func: Callable[[CeleryOrderedTaskGroup], Dict[str, Any]] = None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.celery_task: CeleryTask = celery_task
        self.extra_text = extra_text
        self.cotg: Optional[CeleryOrderedTaskGroup] = None
        if isinstance(self.celery_task, CeleryOrderedTaskGroup):
            self.cotg = self.celery_task
        else:
            self.cotg = CeleryOrderedTaskGroup(
                name=self.celery_task.get_name(),
                tasks=[self.celery_task],
            )

        self.get_kwargs_func = get_kwargs_func
        if not self.get_kwargs_func:
            self.get_kwargs_func = lambda *_, **__: {}

        self.show_download_button = show_download_button
        self.collapsable = collapsable
        self.collapsed = True
        self.interval_duration = interval_duration
        self.render_interval = render_interval

        # download content is used to store the result of the celery task
        self.download_content = None
        self.download_file_format = download_file_format

        # download string is used to store the dcc.send_string output - this is used to trigger the download
        self.download_string = None
        self.in_progress = False
        self.extra_buttons = extra_buttons or []

        if self.show_download_button:
            self.download_formatter_func = download_formatter_func

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        instance: CeleryTaskControls = instance
        cotg: CeleryOrderedTaskGroup = instance.cotg
        from base_dash_app.services.celery_handler_service import CeleryHandlerService
        celery_service: CeleryHandlerService = instance.get_service(CeleryHandlerService)
        instance.download_string = None

        if cotg.redis_client:
            cotg.refresh_all()
            if cotg.get_status() == StatusesEnum.SUCCESS:
                instance.download_content = cotg.get_result()
        if triggering_id.startswith(RELOAD_CELERY_TASK_BTN_ID):
            instance.in_progress = True
            instance.task = celery_service.submit_celery_task(
                celery_task=cotg,
                prev_result_uuids=[],
                **instance.get_kwargs_func(cotg)
            )
        elif triggering_id.startswith(CELERY_CONTROLS_EXPAND_BTN_ID):
            instance.collapsed = not instance.collapsed
        elif triggering_id.startswith(CELERY_TASK_DOWNLOAD_BTN_ID):
            cotg.refresh_all()
            result = cotg.get_result()

            # determine point of this:
            # instance.download_string = instance.download_content

            # hydrate celery task, get result, convert to desired format using download_formatter_func
            # then send as dcc.send_string

            instance.download_content = instance.download_formatter_func(result)

            instance.download_string = dcc.send_string(
                instance.download_content,
                filename=f"{CeleryOrderedTaskGroup.get_start_time(self=cotg, with_refresh=True)}"
                         f"_{cotg.get_name()}"
                         f".{instance.download_file_format}",
            )

        if instance.cotg.get_status() not in StatusesEnum.get_non_terminal_statuses() and instance.in_progress:
            instance.in_progress = False

        return [instance.__render_controls()]

    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=RELOAD_CELERY_TASK_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=CELERY_TASK_DOWNLOAD_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=CELERY_TASK_INTERVAL_ID,
                    input_property="n_intervals",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=CELERY_CONTROLS_EXPAND_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            )
        ]

    def render(self, override_style=None, extra_text=None):
        if override_style is None:
            override_style = {}

        return html.Div(
            children=[
                self.__render_controls(
                    extra_text=extra_text or self.extra_text,
                )
            ],
            style={
                "position": "relative",
                "float": "left",
                "width": "100%",
                "minWidth": "560px",
                "minHeight": "85px",
                **override_style,
            },
            id={"type": CeleryTaskControls.get_wrapper_div_id(), "index": self._instance_id}
        )

    def __render_controls(self, extra_text=None):
        other_buttons = []
        if self.collapsable:
            other_buttons.append(
                dbc.Button(
                    html.I(className="fa-solid fa-chevron-down") if self.collapsed
                    else html.I(className="fa-solid fa-chevron-up"),
                    id={
                        "type": CELERY_CONTROLS_EXPAND_BTN_ID,
                        "index": self._instance_id,
                    },
                    style={
                        "position": "relative",
                        "float": "left",
                        "minWidth": "65px",
                        "fontSize": "25px",
                    },
                    color="dark",
                    outline=True,
                )
            )

        download_string = self.download_string
        self.download_string = None

        return html.Div(
            children=[
                dcc.Interval(
                    id={"type": CELERY_TASK_INTERVAL_ID, "index": self._instance_id},
                    interval=self.interval_duration,
                    n_intervals=0,
                    disabled=(
                        not self.render_interval
                        or self.celery_task.get_status() in StatusesEnum.get_terminal_statuses()
                    ) and not self.in_progress,
                ),
                html.Div(
                    children=[
                        html.Div(
                            f"{self.celery_task.get_name()}",
                            style={
                                "paddingTop": "17px",
                                "paddingBottom": "10px" if self.extra_text else "17px",
                                "fontSize": "24px",
                                "fontWeight": "bold",
                                "position": "relative",
                                "float": "left",
                                "minWidth": "100px",
                            },
                        ),
                        html.Div(
                            f"{extra_text}",
                            style={
                                "paddingBottom": "10px",
                                "fontSize": "16px",
                                "position": "relative",
                                "float": "left",
                                "clear": "left",
                            }
                        ) if extra_text else None,
                        construct_down_ref_btgrp(
                            download_btn_id={
                                "type": CELERY_TASK_DOWNLOAD_BTN_ID,
                                "index": self._instance_id,
                            },
                            hide_download_button=not self.show_download_button,
                            download_content=download_string,
                            download_content_id={
                                "type": CELERY_TASK_DOWNLOAD_CONTENT_ID,
                                "index": self._instance_id,
                            },
                            disable_download_btn=self.download_content is None,
                            reload_btn_id={
                                "type": RELOAD_CELERY_TASK_BTN_ID,
                                "index": self._instance_id,
                            },
                            disable_reload_btn=(
                                self.in_progress
                                or self.celery_task.get_status() in StatusesEnum.get_non_terminal_statuses()
                            ),
                            reload_in_progress=(
                                self.in_progress
                                or self.celery_task.get_status() in StatusesEnum.get_non_terminal_statuses()
                            ),
                            reload_progress=self.celery_task.get_progress(),
                            wrapper_style={
                                "position": "relative",
                                "float": "left",
                                "margin": "0",
                                "clear": "left",
                            },
                            last_load_time=self.celery_task.get_start_time(with_refresh=True),
                            other_buttons=other_buttons + self.extra_buttons,
                            right_align=False,
                        ),
                    ],
                    style={
                        "width": "100%",
                        "display": "inline",
                        "position": "relative",
                        "float": "left",
                        "marginBottom": "20px"
                    },
                ),
                self.celery_task.render() if not self.collapsed else None,
            ]
        )
