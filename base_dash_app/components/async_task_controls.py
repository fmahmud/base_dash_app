import json
from typing import Optional

from dash import html, dcc
import dash_bootstrap_components as dbc

from base_dash_app.components.base_component import ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.datatable.download_and_reload_bg import construct_down_ref_btgrp
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncTask, AsyncGroupProgressContainer, AsyncHandlerService, \
    AsyncWorkProgressContainer, AsyncOrderedTaskGroup

ASYNC_CONTROLS_EXPAND_BTN_ID = "ASYNC_CONTROLS_EXPAND_BTN_ID"

RELOAD_ASYNC_TASK_BTN_ID = "RELOAD_ASYNC_TASK_BTN_ID"

ASYNC_TASK_DOWNLOAD_CONTENT_ID = "ASYNC_TASK_DOWNLOAD_CONTENT_ID"

ASYNC_TASK_DOWNLOAD_BTN_ID = "download-async-task-controls-btn-id"

ASYNC_TASK_INTERVAL_ID = "async-task-interval-id"


class AsyncTaskControls(ComponentWithInternalCallback):
    def __init__(
            self,
            async_task: AsyncTask,
            extra_text=None,
            show_download_button=True,
            collapsable=True,
            interval_duration=1000,
            render_interval=True,
            download_formatter_func=lambda x: json.dumps(x),
            download_file_format="json",
            extra_buttons=None,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.async_task: AsyncTask = async_task
        self.extra_text = extra_text
        self.aotg: Optional[AsyncOrderedTaskGroup] = None
        if isinstance(self.async_task, AsyncOrderedTaskGroup):
            self.aotg = self.async_task
        else:
            self.aotg = AsyncOrderedTaskGroup(
                async_tasks=[self.async_task],
                task_group_title=self.async_task.get_name(),
            )

        self.show_download_button = show_download_button
        self.collapsable = collapsable
        self.collapsed = True
        self.interval_duration = interval_duration
        self.render_interval = render_interval
        self.download_content = None
        self.download_file_format = download_file_format

        self.download_string = None
        self.in_progress = False
        self.extra_buttons = extra_buttons or []

        if self.show_download_button:
            self.download_formatter_func = download_formatter_func

            def final_task_func(wpc: AsyncWorkProgressContainer, task_input, kwargs):
                try:
                    self.download_content = dcc.send_string(
                        self.download_formatter_func(task_input),
                        filename=f"{self.async_task.get_start_time()}"
                                 f"_{self.async_task.get_name()}"
                                 f".{self.download_file_format}",
                    )
                    wpc.complete()
                except Exception as e:
                    wpc.complete(status=StatusesEnum.FAILURE, status_message=str(e))
                    raise e
                finally:
                    self.in_progress = False

            final_task = AsyncTask(
                work_func=final_task_func,
                task_name="Capture output for download",
                is_hidden=True,
            )

            self.aotg.add_task(final_task)

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        instance: AsyncTaskControls = instance
        aotg: AsyncOrderedTaskGroup = instance.aotg
        async_service: AsyncHandlerService = instance.get_service(AsyncHandlerService)
        instance.download_string = None
        if triggering_id.startswith(RELOAD_ASYNC_TASK_BTN_ID):
            instance.in_progress = True
            instance.task = async_service.submit_async_task(aotg)
        elif triggering_id.startswith(ASYNC_CONTROLS_EXPAND_BTN_ID):
            instance.collapsed = not instance.collapsed
        elif triggering_id.startswith(ASYNC_TASK_DOWNLOAD_BTN_ID):
            instance.download_string = instance.download_content

        if instance.aotg.get_status() != StatusesEnum.IN_PROGRESS and instance.in_progress:
            instance.in_progress = False

        return [instance.__render_controls()]

    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=RELOAD_ASYNC_TASK_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=ASYNC_TASK_DOWNLOAD_BTN_ID,
                    input_property="n_clicks",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=ASYNC_TASK_INTERVAL_ID,
                    input_property="n_intervals",
                ),
                states=[]
            ),
            InputToState(
                input_mapping=InputMapping(
                    input_id=ASYNC_CONTROLS_EXPAND_BTN_ID,
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
            id={"type": AsyncTaskControls.get_wrapper_div_id(), "index": self._instance_id}
        )

    def __render_controls(self, extra_text=None):
        other_buttons = []
        if self.collapsable:
            other_buttons.append(
                dbc.Button(
                    html.I(className="fa-solid fa-chevron-down") if self.collapsed
                    else html.I(className="fa-solid fa-chevron-up"),
                    id={
                        "type": ASYNC_CONTROLS_EXPAND_BTN_ID,
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
                    id={"type": ASYNC_TASK_INTERVAL_ID, "index": self._instance_id},
                    interval=self.interval_duration,
                    n_intervals=0,
                    disabled=(
                            not self.render_interval or
                            self.async_task.get_status() != StatusesEnum.IN_PROGRESS
                    ) and not self.in_progress,
                ),
                html.Div(
                    children=[
                        html.Div(
                            f"{self.async_task.get_name()}",
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
                                "type": ASYNC_TASK_DOWNLOAD_BTN_ID,
                                "index": self._instance_id,
                            },
                            hide_download_button=not self.show_download_button,
                            download_content=download_string,
                            download_content_id={
                                "type": ASYNC_TASK_DOWNLOAD_CONTENT_ID,
                                "index": self._instance_id,
                            },
                            disable_download_btn=self.download_content is None,
                            reload_btn_id={
                                "type": RELOAD_ASYNC_TASK_BTN_ID,
                                "index": self._instance_id,
                            },
                            disable_reload_btn=self.in_progress or self.async_task.get_status() == StatusesEnum.IN_PROGRESS,
                            reload_in_progress=self.in_progress or self.async_task.get_status() == StatusesEnum.IN_PROGRESS,
                            reload_progress=self.async_task.get_progress(),
                            wrapper_style={
                                "position": "relative",
                                "float": "left",
                                "margin": "0",
                                "clear": "left",
                            },
                            last_load_time=self.async_task.get_start_time(),
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
                self.async_task.render() if not self.collapsed else None,
            ]
        )
