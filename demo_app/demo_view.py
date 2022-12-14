import datetime
import random
import random
import re
import time
from typing import List, Dict

import dash_bootstrap_components as dbc
import finnhub
from dash import html
from dash.dash_table.Format import Format, Scheme
from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import Session

from base_dash_app.components.alerts import Alert
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.cards.special_cards.job_card import JobCard
from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpSparklineStatCard, TimePeriodsEnum, \
    TsdpAggregationFuncs
from base_dash_app.components.data_visualization import ratio_bar
from base_dash_app.components.data_visualization.ratio_bar import StatusToCount
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.components.lists.todo_list.todo_list import TodoList
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.models.task import Task
from base_dash_app.services.base_service import BaseService
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.views.base_view import BaseView
from base_dash_app.components.labelled_value_chip import LabelledValueChip
from base_dash_app.components.cards.stat_sparkline_card import StatSparklineCard
from base_dash_app.components.cards.statistic_card import StatisticCard
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable
from base_dash_app.virtual_objects.job_parameter import JobParameterDefinition
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.time_series_data_point import TimeSeriesDataPoint
from demo_app.demo_api import DemoApi

DEMO_TABS_DIV_ID = "demo-tabs-div-id"

RUN_TEST_JOB_BTN_ID = "run-test-job-btn-id"

SEARCH_BAR_ID = "search-bar-id"

SEARCH_BUTTON_ID = "search-button-id"

SEARCH_RESULT_DIV_ID = "search-result-div-id"

TEST_ALERT_BTN_ID = "test-alert-btn-id"


class MySelectableModel(BaseModel, Selectable):
    __tablename__ = "my_selectables"

    id = Column(Integer, Sequence("my_selectables_id_seq"), primary_key=True)
    name = Column(String)

    def __lt__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def get_label(self):
        return self.name

    def get_value(self):
        return self.id


class MySelectablesService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(
            object_type=MySelectableModel,
            **kwargs
        )


class TestJobDef(JobDefinition):
    __mapper_args__ = {
        "polymorphic_identity": "TestJobDef"
    }

    @classmethod
    def get_cached_selectables_by_param_name(cls, variable_name, session: Session):
        if variable_name == "param_4":
            all_selectables = session.query(MySelectableModel).all()
            return [CachedSelectable.from_selectable(s) for s in all_selectables]

    @classmethod
    def force_update(cls):
        return True

    @classmethod
    def construct_instance(cls, **kwargs):
        instance = TestJobDef(**kwargs)
        instance.name = "Test Job Definition"
        instance.job_class = "TestJobDef"
        instance.parameters = TestJobDef.get_general_params()
        for param in instance.parameters:
            param.job_definition = instance

        instance.description = "A test job that showcases the capabilities of a job definition, and how to extend it."\
                               " This job doesn't actually do anything. It has a ~50% chance of failure."
        return instance

    @classmethod
    def autoinitialize(cls):
        return True

    @classmethod
    def get_general_params(cls):
        jdp1 = JobDefinitionParameter()
        jdp1.user_facing_param_name = "Param 1"
        jdp1.set_param_type(str)
        jdp1.variable_name = "param_1"
        jdp1.placeholder = "Some string"

        jdp2 = JobDefinitionParameter()
        jdp2.user_facing_param_name = "Param 2"
        jdp2.set_param_type(int)
        jdp2.variable_name = "param_2"
        jdp2.placeholder = "Some integer"

        jdp3 = JobDefinitionParameter()
        jdp3.user_facing_param_name = "Param 3"
        jdp3.set_param_type(bool)
        jdp3.variable_name = "param_3"
        jdp3.placeholder = "Some Boolean"

        jdp4 = JobDefinitionParameter()
        jdp4.user_facing_param_name = "Param 4"
        jdp4.set_param_type(Selectable)
        jdp4.variable_name = "param_4"
        jdp4.placeholder = "Some Selectable"

        return [jdp1, jdp2, jdp3, jdp4]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check_completion_criteria(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        return prog_container.execution_status

    def check_prerequisites(self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict, **kwargs) -> StatusesEnum:
        self.info_log("starting prereq. check")
        self.info_log("Example info log")
        self.debug_log("Example debug log")
        self.critical_log("Example critical log")
        self.warn_log("Example warn log")
        self.error_log("Example error log")

        prog_container.result = 1
        return StatusesEnum.SUCCESS

    def start(self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict, **kwargs) -> StatusesEnum:
        if "session" not in kwargs:
            prog_container.end_reason = "Didn't receive session!"
            self.critical_log("Didn't receive session.")
            return StatusesEnum.FAILURE

        session: Session = kwargs["session"]

        time.sleep(1)
        prog_container.progress += 20
        self.info_log("1 second passed")
        time.sleep(1)
        prog_container.progress += 20
        self.info_log("2 seconds passed")
        time.sleep(1)
        prog_container.progress += 20
        self.info_log("3 seconds passed")
        time.sleep(1)
        prog_container.progress += 20
        self.info_log("4 seconds passed")

        if "param_4" in parameter_values:
            my_selectable: MySelectableModel = session.query(MySelectableModel)\
                .filter_by(id=int(parameter_values["param_4"])).first()
            self.info_log(my_selectable.get_label())


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
            "Demo View", re.compile("^/demo$|^/$"), show_in_navbar=True, nav_url="/demo", **kwargs,
            input_to_states_map=[
                InputToState(
                    input_mapping=InputMapping(
                        input_id=TEST_ALERT_BTN_ID,
                        input_property="n_clicks"
                    ),
                    states=[]
                ),
                InputToState(
                    input_mapping=InputMapping(
                        input_id=SEARCH_BUTTON_ID,
                        input_property="n_clicks"
                    ),
                    states=[
                        StateMapping(
                            state_id=SEARCH_BAR_ID,
                            state_property="value"
                        )
                    ]
                )
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
        self.data_tables = []
        self.current_tab_id = 'tab-0'

    def validate_state_on_trigger(self):
        return

    def handle_any_input(self, *args, triggering_id, index):
        if triggering_id.startswith(TEST_ALERT_BTN_ID):
            self.push_alert(Alert("Test Alert!"))
        elif triggering_id.startswith(SEARCH_BUTTON_ID):
            state_mapping = self.get_callback_state(SEARCH_BUTTON_ID, args)
            search_value = state_mapping[SEARCH_BAR_ID]

            stock_quote = self.finnhub_client.quote(search_value)
            if "c" in stock_quote and "o" in stock_quote:
                stock_quote['symbol'] = search_value
                self.watchlist.append(stock_quote)

        job_def_service: JobDefinitionService = self.get_service(JobDefinitionService)
        job_def: TestJobDef = job_def_service.get_by_id(self.test_job_id)

        return [
            DemoView.raw_render(
                self.watchlist,
                job_def,
                job_def_service
            )
        ]

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
    def raw_render(
            watchlist, job: JobDefinition, job_def_service: JobDefinitionService,
            data_tables: List[DataTableWrapper] = None,
            current_tab_id: str = 'tab-0'
    ):
        # return todo_list_component.render()
        if data_tables is None:
            data_tables = []

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

        tabs_div = dbc.Tabs(
            id=DEMO_TABS_DIV_ID,
            active_tab=current_tab_id,
            children=[
                dbc.Tab(
                    children=[
                        JobCard(job, job_def_service, footer="footer").render()
                    ],
                    label="Job Card Demo",
                    style={"padding": "20px"}
                ),
                dbc.Tab(
                    children=[
                        StatisticCard(
                            title="Test Statistic Card",
                            values=[
                                LabelledValueChip(label="Test Label", value="234"),
                                LabelledValueChip(label="Test Label", value=1235),
                                LabelledValueChip(label="Test Label", value="True"),
                                LabelledValueChip(label="Test Label", value=203.2),
                                LabelledValueChip(label="out of view", value="This value won't be rendered"),
                            ]
                        ).render(),
                        StatSparklineCard(
                            title="Sparkline Test Stat Card",
                            graph_height=155,
                            values=[
                                LabelledValueChip(label="Annually", value=90.4),
                                LabelledValueChip(label="Monthly", value=96.3),
                                LabelledValueChip(label="Weekly", value=100),
                                LabelledValueChip(label="Daily", value=100)
                            ],
                            series=[
                                TimeSeriesDataPoint(
                                    date=datetime.datetime(year=2022, month=11, day=1) + datetime.timedelta(days=i),
                                    value=50 - ((random.random() / (i / 3 + 1)) * 50) + 50
                                )
                                for i in range(50)
                            ]
                        ).render(),
                        TsdpSparklineStatCard(
                            title="Test TSDP Sparkline Card",
                            graph_height=155,
                            series=[
                                TimeSeriesDataPoint(
                                    date=datetime.datetime(year=2022, month=11, day=1) + datetime.timedelta(days=i),
                                    value=50000 - ((random.random() / (i / 3 + 1)) * 50) + 50
                                )
                                for i in range(50)
                            ],
                            time_periods_to_show=[
                                TimePeriodsEnum.LAST_24HRS,
                                TimePeriodsEnum.LAST_7_DAYS,
                                TimePeriodsEnum.LAST_30_DAYS,
                            ],
                            aggregation_to_use=TsdpAggregationFuncs.SUM
                        ).render()
                    ],
                    label="Stats Card Demo",
                    style={"padding": "20px"}
                ),
                dbc.Tab(
                    children=[
                        html.Div(
                            children=[dtw.render() for dtw in data_tables],
                            style={"position": "relative", "float": "left", "clear": "left", "width": "100%"}
                        )
                    ],
                    label="Data Table Demo",
                    style={"padding": "20px"}
                )
            ],
            style={
                "position": "relative",
                "float": "left",
                "clear": "left",
                "width": "100%",
                "overflow": "scroll",
                "marginTop": "20px",
            }
        )

        return html.Div(
            children=[
                dbc.Button("Test Alerts", id=TEST_ALERT_BTN_ID, style=test_button_style),
                search_bar,
                html.Div(
                    children=DemoView.render_watchlist(watchlist),
                    id=SEARCH_RESULT_DIV_ID,
                    style={"marginTop": "40px"}
                ),
                ratio_bar.render_from_stc_list([
                    StatusToCount(state_name="A", count=5, color=StatusesEnum.PENDING),
                    StatusToCount(state_name="B", count=5, color=StatusesEnum.IN_PROGRESS)
                ]),
                tabs_div
            ],
            style={"maxWidth": "1280px", "margin": "0 auto", "padding": "20px"}
        )

    def render(self, query_params, *args):
        session: Session = self.dbm.get_session()
        current_selectables = session.query(MySelectableModel).all()
        if len(current_selectables) == 0:
            for i in range(10):
                new_selectable_model: MySelectableModel = MySelectableModel()
                new_selectable_model.name = f"MySelectableModel{i}"
                session.add(new_selectable_model)

            try:
                session.commit()
            except:
                session.rollback()

        job_def_service: JobDefinitionService = self.get_service(JobDefinitionService)
        self.logger.debug("This is debug log")
        self.logger.info("This is info log")
        self.logger.warn("This is warn log")
        self.logger.error("This is error log")
        self.logger.critical("This is critical log")

        if len(self.data_tables) == 0:
            numeric_format = Format(precision=2, scheme=Scheme.fixed).group(True)
            dtw: DataTableWrapper = DataTableWrapper(
                title="Data Table 1 ",
                columns=[
                    {"id": f"{i}", "type": "numeric", "format": numeric_format, "name": f"Column {i}"}
                    for i in range(10)
                ]
            )

            def fill_data(*args, **kwargs):
                data = []
                for row in range(100):
                    row_data = {f"{col}": random.random() * 100 for col in range(10)}
                    data.append(row_data)

                return data

            dtw.set_data(fill_data())
            dtw.reload_data_function = fill_data

            self.data_tables.append(dtw)

        return html.Div(
            children=DemoView.raw_render(
                self.watchlist,
                job_def_service.get_by_id(self.test_job_id),
                job_def_service,
                data_tables=self.data_tables,
            ),
            id=self.wrapper_div_id
        )