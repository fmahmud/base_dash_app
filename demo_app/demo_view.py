import datetime
import random
import re
import time
from typing import Callable, List

from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session

from base_dash_app.components.alerts import Alert
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.cards.special_cards.job_card import JobCard
from base_dash_app.components.data_visualization import ratio_bar
from base_dash_app.components.data_visualization.ratio_bar import StatusToCount
from base_dash_app.components.details import details
from base_dash_app.components.details.details import DetailTextItem
from base_dash_app.components.lists.todo_list.todo_list import TodoList
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.models.task import Task
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.views.base_view import BaseView
from dash import html
import dash_bootstrap_components as dbc
import finnhub

from base_dash_app.virtual_objects.job_parameter import JobParameterDefinition

RUN_TEST_JOB_BTN_ID = "run-test-job-btn-id"

SEARCH_BAR_ID = "search-bar-id"

SEARCH_BUTTON_ID = "search-button-id"

SEARCH_RESULT_DIV_ID = "search-result-div-id"

TEST_ALERT_BTN_ID = "test-alert-btn-id"


class TestJobDef(JobDefinition):
    parameters = [
        JobParameterDefinition(param_name="Param 1", param_type=str, required=True, variable_name="param_1"),
        JobParameterDefinition(param_name="Param 2", param_type=int, variable_name="param_2"),
        JobParameterDefinition(param_name="Param 3", param_type=bool, variable_name="param_3"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            description="This is a test job that doesn't do anything. It has a 50% chance of failure.",
            **kwargs
        )

    def check_completion_criteria(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        return prog_container.execution_status

    def check_prerequisites(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        self.logger.info("starting prereq. check")

        if "session" not in kwargs:
            prog_container.end_reason = "Session not found in kwargs."
            return StatusesEnum.FAILURE

        prog_container.result = 1
        return StatusesEnum.SUCCESS

    def start(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        time.sleep(1)
        prog_container.progress += 20
        time.sleep(1)
        prog_container.progress += 20
        time.sleep(1)
        prog_container.progress += 20
        time.sleep(1)
        prog_container.progress += 20
        time.sleep(1)
        ran = random.random()
        if ran < 0.5:
            prog_container.end_reason = "Failed Successfully!"
            return StatusesEnum.FAILURE
        else:
            prog_container.end_reason = "Everything succeeded!"
            prog_container.progress += 20
            time.sleep(1)
            return StatusesEnum.SUCCESS

    def stop(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        pass

    @classmethod
    def get_parameters(cls) -> List[JobParameterDefinition]:
        return TestJobDef.parameters


class DemoView(BaseView):
    def __init__(self, **kwargs):
        super().__init__(
            "Demo View", re.compile("^/demo$"), show_in_navbar=True, nav_url="/demo", **kwargs,
            input_to_states_map=[
                InputToState(
                    input_mapping=InputMapping(
                        input_id=TEST_ALERT_BTN_ID,
                        input_property="n_clicks"
                    ),
                    states=[]
                ),
            ]
        )
        self.todo_list_component = TodoList(
            self.register_callback_func,
            [
                Task("Item 1", "Do item 1 really well."),
                Task("Item 2", "Do item 2 really well."),
                Task("Item 3", "Do item 2 really well."),
            ]
        )

        self.watchlist = []
        self.finnhub_client = finnhub.Client(api_key="c7o457qad3idf06mmdc0")

        self.test_job_id = 1
        # self.register_callback_func(
        #     output=Output(SEARCH_RESULT_DIV_ID, "children"),
        #     inputs=[Input(SEARCH_BUTTON_ID, "n_clicks")],
        #     state=[State(SEARCH_BAR_ID, "value")],
        #     function=self.handle_search.__get__(self, self.__class__)
        # )

    def validate_state_on_trigger(self):
        return

    def handle_any_input(self, *args, triggering_id, index):
        if triggering_id.startswith(TEST_ALERT_BTN_ID):
            self.push_alert(Alert("Test Alert!"))

        job_def_service: JobDefinitionService = self.get_service(JobDefinitionService)
        job_def: JobDefinition = job_def_service.get_by_id(self.test_job_id)

        return [
            DemoView.raw_render(
                self.watchlist,
                job_def,
                job_def_service
            )
        ]

    def handle_search(self, n_clicks, search_value):
        if n_clicks == 0 or n_clicks is None:
            raise PreventUpdate()
        if search_value is None or search_value == '':
            raise PreventUpdate()

        stock_quote = self.finnhub_client.quote(search_value)
        if "c" in stock_quote and "o" in stock_quote:
            stock_quote['symbol'] = search_value
            self.watchlist.append(stock_quote)

        return DemoView.render_watchlist(self.watchlist)

    @staticmethod
    def render_watchlist(watchlist):
        base_style = {"position": "relative", "float": "left", "minWidth": "100px", "maxWidth": "300px", "marginRight": "10px"}
        return [
            dbc.Card(
                children=[
                    html.Div(children=stock['symbol'], style=base_style),
                    html.Div(children="C: %f" % stock['c'], style=base_style),
                    html.Div(children="O: %f" % stock['o'], style=base_style),
                    html.Div(children="H: %f" % stock['h'], style=base_style),
                    html.Div(children="L: %f" % stock['l'], style=base_style),
                    html.Div(children="PC: %f" % stock['pc'], style=base_style),
                ],
                body=True,
                style={"flexDirection": "row", "background": "red" if stock["c"] < stock["o"] else "green"}
            )
            for stock in watchlist
        ]

    @staticmethod
    def raw_render(watchlist, job: JobDefinition, job_def_service: JobDefinitionService):
        # return todo_list_component.render()

        search_bar = dbc.Row(
            [
                dbc.Input(type="search", placeholder="Search",
                          id=SEARCH_BAR_ID,
                          style={"width": "1000px", "height": "50px", "fontSize": "24px", "padding": "10px"}),
                dbc.Button(
                    "Search", color="primary", className="ms-2", n_clicks=0,
                    id=SEARCH_BUTTON_ID,
                    style={"maxWidth": "230px", "height": "50px"}
                ),
            ],
            className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
            align="center",
        )

        test_button_style = {"position": "relative", "float": "left", "margin": "10px"}

        return html.Div(
            children=[
                dbc.Button("Test Alerts", id=TEST_ALERT_BTN_ID, style=test_button_style),
                JobCard(job, job_def_service).render(),
                search_bar,
                html.Div(children=[], id=SEARCH_RESULT_DIV_ID, style={"marginTop": "40px"}),
                ratio_bar.render_from_stc_list([
                    StatusToCount(state_name="A", count=5, color=StatusesEnum.PENDING),
                    StatusToCount(state_name="B", count=5, color=StatusesEnum.IN_PROGRESS)
                ])
            ],
            style={"maxWidth": "1280px", "margin": "0 auto", "padding": "20px"}
        )

    def render(self, query_params, *args):
        job_def_service: JobDefinitionService = self.get_service(JobDefinitionService)

        return html.Div(
            children=DemoView.raw_render(
                self.watchlist,
                job_def_service.get_by_id(self.test_job_id),
                job_def_service,
            ),
            id=self.wrapper_div_id
        )