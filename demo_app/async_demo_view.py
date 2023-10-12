import datetime
import json
import pprint
import random
import re
import time
from typing import List, Any, Dict

import dash_bootstrap_components as dbc
from celery import shared_task
from dash import html, dcc

from base_dash_app.components.async_task_controls import AsyncTaskControls
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.celery_task_controls import CeleryTaskControls
from base_dash_app.components.data_visualization.simple_area_graph import AreaGraph
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncOrderedTaskGroup, AsyncTask, AsyncWorkProgressContainer, \
    AsyncHandlerService, AsyncUnorderedTaskGroup
from base_dash_app.utils import tsdp_utils
from base_dash_app.utils.tsdp_utils import get_max_for_each_moment
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.async_vos.celery_task import CeleryOrderedTaskGroup, CeleryTask, \
    CeleryUnorderedTaskGroup
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from demo_app import celery_tasks

ASYNC_VIEW_INTERVAL_ID = "async-view-interval-id"

START_ASYNC_GROUP_TASKS = "start-async-group-tasks-btn-id"


class AsyncDemoView(BaseView):
    def __init__(self, **kwargs):
        super().__init__(
            title="Async Demo View",
            url_regex=re.compile("$a"),
            show_in_navbar=False,
            input_to_states_map=[
                # InputToState(
                #     input_mapping=InputMapping(
                #         input_id=START_ASYNC_GROUP_TASKS,
                #         input_property="n_clicks",
                #     ),
                #     states=[],
                # ),
                InputToState(
                    input_mapping=InputMapping(
                        input_id=ASYNC_VIEW_INTERVAL_ID,
                        input_property="n_intervals",
                    ),
                    states=[],
                )
            ],
            **kwargs
        )

        self.task_controls = []
        self.celery_groups = []

        if len(self.celery_groups) == 0:
            self.celery_groups = [
                CeleryOrderedTaskGroup(
                    name="Ordered Task Group 1",
                    tasks=[
                        CeleryTask(
                            name="Celery Task 1 ",
                            work_func=celery_tasks.gen_graph_data,
                        ),
                        CeleryTask(
                            name="Celery Task 2",
                            work_func=celery_tasks.gen_graph_data
                        ),
                        CeleryOrderedTaskGroup(
                            name="Ordered Task Group 2",
                            tasks=[
                                CeleryTask(
                                    name="Task 3",
                                    work_func=celery_tasks.gen_graph_data
                                ),
                                CeleryTask(
                                    name="Task 4",
                                    work_func=celery_tasks.gen_graph_data
                                ),
                            ]
                        ),
                        CeleryUnorderedTaskGroup(
                            require_all_success=True,
                            name="Unordered Task Group 2",
                            tasks=[
                                CeleryTask(
                                    name="Task 5",
                                    work_func=celery_tasks.gen_graph_data
                                ),
                                CeleryTask(
                                    name="Task 5",
                                    work_func=celery_tasks.gen_graph_data
                                ),
                                CeleryTask(
                                    name="Task 5",
                                    work_func=celery_tasks.gen_graph_data
                                ),
                                # CeleryTask(
                                #     name="Long Sleep Task",
                                #     work_func=celery_tasks.long_sleep_task
                                # ),
                                # CeleryTask(
                                #     name="Failure Task",
                                #     work_func=celery_tasks.throw_exception_func
                                # ),
                            ],
                            reducer_task=combine_series  # not sure why this is highlighted
                        )
                    ]
                )
            ]

            if self.task_controls is None or len(self.task_controls) == 0:
                self.task_controls = []
                for cg in self.celery_groups:
                    ctc: CeleryTaskControls = CeleryTaskControls(
                        **self.produce_kwargs(),
                        celery_task=cg,
                        show_download_button=True,
                        download_formatter_func=lambda x: tsdp_utils.tsdp_array_to_csv(
                            tsdp_array=tsdp_utils.deserialize_tsdp_array(x)
                        ),
                        download_file_format="csv",
                        right_align=True,
                        show_stop_button=True
                    )
                    self.task_controls.append(ctc.render(override_style={"width": "560px"}))

    def validate_state_on_trigger(self):
        return

    def handle_any_input(self, *args, triggering_id, index):
        for cg in self.celery_groups:
            if cg.redis_client:
                cg.refresh_all()

        return [AsyncDemoView.raw_render(self.celery_groups, self.task_controls)]

    @staticmethod
    def raw_render(celery_groups: List[CeleryOrderedTaskGroup], task_controls: List[CeleryTaskControls]):
        area_graph = AreaGraph()

        for cg in celery_groups:
            # for at in ag.work_containers:
            if cg.get_status() == StatusesEnum.SUCCESS:
                list_of_dicts = cg.get_result()

                area_graph.add_series(
                    graphables=sorted([
                        TimeSeriesDataPoint().from_dict(d) for d in list_of_dicts
                    ]),
                    name=cg.get_name()
                )

        disabled = (all(cg is None or cg.get_status() != StatusesEnum.IN_PROGRESS for cg in celery_groups))

        return html.Div(
            children=[
                *task_controls,
                # dbc.Button("Reload Graph", id=START_ASYNC_GROUP_TASKS),
                dcc.Interval(
                    id=ASYNC_VIEW_INTERVAL_ID,
                    interval=1000,
                    n_intervals=0,
                    disabled=disabled
                ),
                area_graph.render(
                    smoothening=0,
                    height=800,
                    style={"width": "100%", "height": "100%", "padding": "20px"}
                )
            ]
        )

    def render(self, *args, **kwargs):
        for cg in self.celery_groups:
            if cg.redis_client:
                cg.refresh_all()

        return html.Div(
            id=self.wrapper_div_id,
            children=AsyncDemoView.raw_render(self.celery_groups, self.task_controls)
        )


@shared_task()
def combine_series(*args, target_uuid: str, prev_result_uuids: List[str], hash_key: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client = RuntimeApplication.get_instance().redis_client

    cutg: CeleryUnorderedTaskGroup = CeleryUnorderedTaskGroup.from_redis(redis_client=redis_client, uuid=target_uuid)
    series: Dict[datetime.datetime, TimeSeriesDataPoint] = {}
    for wc in cutg.work_containers:
        redis_content = redis_client.hget(wc.uuid, hash_key) or "[]"
        data_array: List[Dict[str, Any]] = json.loads(redis_content)
        tsdp_array: List[TimeSeriesDataPoint] = tsdp_utils.deserialize_tsdp_array(data_array)

        for tsdp in tsdp_array:
            if tsdp.date in series:
                series[tsdp.date].value += tsdp.value
            else:
                series[tsdp.date] = tsdp

    cutg.set_result(tsdp_utils.serialize_tsdp_array(list(series.values())))

