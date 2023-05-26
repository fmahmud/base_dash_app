import datetime
import random
import re
import time
from typing import List

import dash_bootstrap_components as dbc
from dash import html, dcc

from base_dash_app.components.async_task_controls import AsyncTaskControls
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.data_visualization.simple_area_graph import AreaGraph
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncOrderedTaskGroup, AsyncTask, AsyncWorkProgressContainer, \
    AsyncHandlerService, AsyncUnorderedTaskGroup
from base_dash_app.utils import tsdp_utils
from base_dash_app.utils.tsdp_utils import get_max_for_each_moment
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint

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
        self.async_groups = []

    def validate_state_on_trigger(self):
        return

    def gen_work_func(self):
        def gen_graph_data(prog_container: AsyncWorkProgressContainer, prev_result=None, *args, **kwargs):
            self.logger.info("Starting work func")
            time.sleep(random.randint(1, 5))
            prog_container.set_progress(25)
            prog_container.set_status_message("Generating Data...")
            time.sleep(1)
            prog_container.set_progress(50)
            time.sleep(random.randint(1, 5))
            prog_container.set_progress(75)
            if prev_result:
                data = prev_result
                for d in data:
                    d.value += random.randint(0, 100)
            else:
                data = [
                    TimeSeriesDataPoint(
                        date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                        value=random.randint(0, 100)
                    )
                    for i in range(100)
                ]
            prog_container.complete(
                result=data
            )
            self.logger.info("Finished work func")

        return gen_graph_data

    def handle_any_input(self, *args, triggering_id, index):
        async_service: AsyncHandlerService = self.get_service(AsyncHandlerService)
        if triggering_id.startswith(START_ASYNC_GROUP_TASKS):

            for ag in self.async_groups:
                async_service.submit_async_task(ag)

        return [AsyncDemoView.raw_render(self.async_groups, self.task_controls)]

    @staticmethod
    def raw_render(async_groups: List[AsyncOrderedTaskGroup], task_controls: List[AsyncTaskControls]):
        area_graph = AreaGraph()

        for ag in async_groups:
            for at in ag.work_containers:
                if at.get_status() == StatusesEnum.SUCCESS:
                    area_graph.add_series(
                        graphables=sorted(at.get_result()),
                        name=at.get_name()
                    )

        disabled = (all(ag is None or ag.get_status() != StatusesEnum.IN_PROGRESS for ag in async_groups))

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
        async_service: AsyncHandlerService = self.get_service(AsyncHandlerService)
        if len(self.async_groups) == 0:
            self.async_groups = [
                AsyncOrderedTaskGroup(
                    task_group_title="Ordered Task Group 1",
                    async_tasks=[
                        AsyncTask(
                            task_name="Task 1",
                            work_func=self.gen_work_func()
                        ),
                        AsyncTask(
                            task_name="Task 2",
                            work_func=self.gen_work_func()
                        ),
                        AsyncOrderedTaskGroup(
                            task_group_title="Ordered Task Group 2",
                            async_tasks=[
                                AsyncTask(
                                    task_name="Task 3",
                                    work_func=self.gen_work_func()
                                ),
                                AsyncTask(
                                    task_name="Task 4",
                                    work_func=self.gen_work_func()
                                ),

                            ]
                        ),
                        AsyncUnorderedTaskGroup(
                            task_group_title="Unordered Task Group 2",
                            async_tasks=[
                                AsyncTask(
                                    task_name="Task 5",
                                    work_func=self.gen_work_func()
                                ),
                                AsyncTask(
                                    task_name="Task 6",
                                    work_func=self.gen_work_func()
                                ),
                            ],
                            async_service=async_service,
                            reducer_func=get_max_for_each_moment
                        )
                    ]
                )
            ]

            if self.task_controls is None or len(self.task_controls) == 0:
                self.task_controls = []
                for ag in self.async_groups:
                    atc: AsyncTaskControls = AsyncTaskControls(
                        **self.produce_kwargs(),
                        async_task=ag,
                        show_download_button=True,
                        download_formatter_func=tsdp_utils.tsdp_array_to_csv,
                        download_file_format="csv",
                    )
                    self.task_controls.append(atc.render(override_style={"width": "560px"}))

        return html.Div(
            id=self.wrapper_div_id,
            children=AsyncDemoView.raw_render(self.async_groups, self.task_controls)
        )