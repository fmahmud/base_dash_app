import datetime
import random
import re
import time
from typing import List, Dict, Optional

import dash_bootstrap_components as dbc
from dash import html
from dash.dash_table.Format import Format, Scheme
from sqlalchemy import Column, Integer, Sequence, String
from sqlalchemy.orm import Session

from base_dash_app.components.alerts import Alert
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping, StateMapping
from base_dash_app.components.cards.full_width_card import ThreeColumnCard
from base_dash_app.components.cards.special_cards.job_card import JobCard
from base_dash_app.components.cards.stat_sparkline_card import StatSparklineCard
from base_dash_app.components.cards.statistic_card import StatisticCard
from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpSparklineStatCard, TsdpStatCardDescriptor
from base_dash_app.components.dashboards.simple_timeseries_dashboard import SimpleTimeSeriesDashboard
from base_dash_app.components.data_visualization.simple_area_graph import AreaGraph
from base_dash_app.components.data_visualization.simple_line_graph import LineGraph, GraphTypes
from base_dash_app.services.async_handler_service import AsyncWorkProgressContainer
from base_dash_app.virtual_objects.timeseries.timeseries_wrapper import TimeSeriesWrapper
from base_dash_app.virtual_objects.timeseries.date_range_aggregation_descriptor import DateRangeAggregatorDescriptor
from base_dash_app.components.data_visualization import ratio_bar
from base_dash_app.components.data_visualization.ratio_bar import StatusToCount
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.components.datatable.time_series_datatable_wrapper import TimeSeriesDataTableWrapper
from base_dash_app.components.labelled_value_chip import LabelledValueChip
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.services.base_service import BaseService
from base_dash_app.services.job_definition_service import JobDefinitionService
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable
from base_dash_app.virtual_objects.job_parameter import JobParameterDefinition
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.timeseries.time_periods_enum import TimePeriodsEnum
from base_dash_app.virtual_objects.timeseries.time_series import TimeSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs

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

        instance.description = "A test job that showcases the capabilities of a job definition, and how to extend it." \
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

    def check_prerequisites(self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
                            **kwargs) -> StatusesEnum:
        self.info_log("starting prereq. check")
        self.info_log("Example info log")
        self.debug_log("Example debug log")
        self.critical_log("Example critical log")
        self.warn_log("Example warn log")
        self.error_log("Example error log")

        prog_container.result = 1
        return StatusesEnum.SUCCESS

    def start(self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
              **kwargs) -> StatusesEnum:
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
            my_selectable: MySelectableModel = session.query(MySelectableModel) \
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
            ],
        )
        self.sub_views = None
        self.simple_tsdp_dash = None
        self.tsdp_datatables = []

        self.watchlist = []

        self.test_job_id = 1
        self.data_tables = []
        self.current_tab_id = 'tab-0'

    def handle_any_input(self, *args, triggering_id, index):
        if triggering_id.startswith(TEST_ALERT_BTN_ID):
            self.push_alert(Alert("Test Default Alert!", duration=10))
            self.push_alert(Alert("Test Warning Alert!", color="warning", duration=5))
            self.push_alert(Alert("Test DANGER Alert!", color="danger", duration=20))

        job_def_service: JobDefinitionService = self.get_service(JobDefinitionService)
        job_def: TestJobDef = job_def_service.get_by_id(self.test_job_id)

        return [
            DemoView.raw_render(
                self.watchlist,
                job_def_service.get_by_id(self.test_job_id),
                job_def_service,
                data_tables=self.data_tables,
                tsdp_data_tables=self.tsdp_datatables,
                simple_tsdp_dash=self.simple_tsdp_dash,
                sub_views=self.sub_views
            )
        ]

    @staticmethod
    def render_watchlist(watchlist):
        base_style = {"position": "relative", "float": "left", "minWidth": "100px", "maxWidth": "300px",
                      "marginRight": "10px"}
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
            tsdp_data_tables: List[TimeSeriesDataTableWrapper] = None,
            simple_tsdp_dash: SimpleTimeSeriesDashboard = None,
            sub_views: Dict[str, BaseView] = None,
            current_tab_id: str = 'tab-0'
    ):
        # return todo_list_component.render()
        if data_tables is None:
            data_tables = []

        if tsdp_data_tables is None:
            tsdp_data_tables = []

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

        extra_views = []
        for name, view in sub_views.items():
            extra_views.append(
                dbc.Tab(
                    label=name,
                    children=[
                        view.render()
                    ],
                ),
            )

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
                    label="Simple Line Graph Demo",
                    children=[
                        LineGraph(title="Line Graph Demo")
                        .add_series(
                            name="Series 1",
                            graphables=[
                                TimeSeriesDataPoint(
                                    date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                                    value=random.randint(0, 100)
                                )
                                for i in range(100)
                            ],
                            graph_type=GraphTypes.BAR,
                            color="tan"
                        )
                        .add_series(
                            name="Series 2",
                            graphables=[
                                TimeSeriesDataPoint(
                                    date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                                    value=random.randint(0, 100) * -1.5
                                )
                                for i in range(100)
                            ],
                            graph_type=GraphTypes.BAR,
                            color="red"
                        )
                        .add_series(
                            name="Series 3",
                            graphables=[
                                TimeSeriesDataPoint(
                                    date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                                    value=random.randint(0, 100000) * 2
                                )
                                for i in range(100)
                            ],
                            secondary_y=True
                        )
                        .render(
                            smoothening=0.7,
                            height=800,
                            style={"width": "100%", "height": "100%", "padding": "20px"}
                        )
                    ],
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
                        ThreeColumnCard().render(
                            column1_content=[
                                html.H1("Test")
                            ],
                            column2_content=TsdpSparklineStatCard(
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
                            ).render(style_override={
                                # "filter": "none"
                            }),
                            column3_content=[],
                            style_override={"height": "330px"}
                        )
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
                ),
                dbc.Tab(
                    label="Time Series Data Table Demo",
                    children=[
                        html.Div(
                            children=[tsdpdtw.render() for tsdpdtw in tsdp_data_tables]
                        )
                    ]
                ),
                dbc.Tab(
                    label="Simple TSDP Dashboard Demo",
                    children=[
                        simple_tsdp_dash.render(
                            wrapper_style_override={
                                "position": "relative", "float": "left", "width": "100%",
                                "padding": "20px"
                            }
                        )
                    ]
                ),
                *extra_views
            ],
            style={
                "position": "relative",
                "float": "left",
                "clear": "left",
                "width": "100%",
                "marginTop": "20px",
                "height": "42px"
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
            style={"margin": "0 auto", "padding": "20px"}
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
                ],
                service_provider=self.get_service
            )

            def fill_data(async_container: Optional[AsyncWorkProgressContainer] = None, **kwargs):
                if async_container is None:
                    async_container = AsyncWorkProgressContainer()

                data = []
                for row in range(100):
                    row_data = {f"{col}": random.random() * 100 for col in range(10)}
                    data.append(row_data)
                    async_container.progress += 0.5
                    if row % 25 == 0:
                        time.sleep(0.5)

                return data

            dtw.set_data(fill_data())
            dtw.reload_data_function = fill_data

            self.data_tables.append(dtw)

        numeric_format = Format(precision=2, scheme=Scheme.fixed).group(True)
        start_date = datetime.datetime(2022, 11, 1)
        end_date = datetime.datetime(2023, 1, 1)
        interval_size = datetime.timedelta(days=1)

        def wrapper_generate_data(num_series, interval, offset=0, sleep_delay=0):
            def generate_data(async_container: Optional[AsyncWorkProgressContainer] = None):
                if async_container is None:
                    async_container = AsyncWorkProgressContainer()

                all_series = []
                for i in range(offset, num_series + offset):
                    timeseries: TimeSeries = TimeSeries(
                        title=f"Series {i + 1}",
                        unique_id=f"series-{i + 1}",
                        unit="$",
                        description="This is a test series"
                    )

                    for i in range((end_date - start_date) // interval + 1):
                        timeseries.add_tsdp(
                            TimeSeriesDataPoint(
                                date=start_date + (i * interval),
                                value=random.random() * 100
                            )
                        )

                    all_series.append(timeseries)
                    async_container.progress += 50.0 / num_series
                    time.sleep(max(sleep_delay, 0))
                return all_series

            return generate_data

        if len(self.tsdp_datatables) == 0:
            tsdp_dtw: TimeSeriesDataTableWrapper = TimeSeriesDataTableWrapper(
                title="Data Table 1",
                start_date=start_date,
                end_date=end_date,
                interval_size=interval_size,
                aggregation_method=TsdpAggregationFuncs.SUM,
                reload_data_function=wrapper_generate_data(2, datetime.timedelta(hours=1))
            )

            timeseries = TimeSeries(
                title=f"Series Hourly",
                unit="SGD",
                unique_id=f"series-1"
            )

            timeseries2 = TimeSeries(
                title=f"Series Hourly 2",
                unit="USD",
                unique_id=f"series-2"
            )

            tsdp_dtw.add_timeseries(
                timeseries=timeseries,
                format=numeric_format,
                datatype="numeric"
            )

            tsdp_dtw.add_timeseries(
                timeseries=timeseries2,
                format=numeric_format,
                datatype="numeric"
            )

            self.tsdp_datatables.append(tsdp_dtw)

        if self.simple_tsdp_dash is None:
            date_range = DateRangeAggregatorDescriptor(
                start_date=start_date,
                end_date=end_date,
                interval=interval_size,
                aggregation_method=TsdpAggregationFuncs.SUM
            )

            tsw1 = TimeSeriesWrapper(
                title=f"Series Hourly",
                unique_id=f"series-3",
                stat_card_descriptors=[
                    TsdpStatCardDescriptor(
                        title="TS 1 Means over Time",
                        graph_height=140,
                        time_periods_to_show=[
                            TimePeriodsEnum.LAST_24HRS, TimePeriodsEnum.LAST_7_DAYS,
                            TimePeriodsEnum.LAST_30_DAYS, TimePeriodsEnum.LATEST
                        ],
                        aggregation_to_use=TsdpAggregationFuncs.SEGMENT_START,
                    ),
                ],
                column_format=numeric_format,
            )

            tsw2 = TimeSeriesWrapper(
                title=f"Series Hourly 2",
                unique_id=f"series-4",
                stat_card_descriptors=[
                    TsdpStatCardDescriptor(
                        title="TS 2 Means over Time",
                        graph_height=210,
                        time_periods_to_show=[
                            TimePeriodsEnum.LAST_24HRS, TimePeriodsEnum.LAST_7_DAYS,
                            TimePeriodsEnum.LAST_30_DAYS, TimePeriodsEnum.LATEST
                        ],
                        aggregation_to_use=TsdpAggregationFuncs.SEGMENT_START,
                        description="This is a very long description."
                                    " Lorem Ipsum is simply dummy text of the printing and typesetting industry."
                                    " Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,",
                        unit="USD",
                        show_expand_button=True
                    ),
                ],
                column_format=numeric_format,
            )

            self.simple_tsdp_dash = SimpleTimeSeriesDashboard(
                title="Test Simple Time Series Dashboard",
                base_date_range=date_range,
                reload_data_function=wrapper_generate_data(2, datetime.timedelta(days=1), offset=2, sleep_delay=1),
                service_provider=self.get_service
            )

            self.simple_tsdp_dash.add_timeseries(tsw1)
            self.simple_tsdp_dash.add_timeseries(tsw2)

        if not self.sub_views:
            from demo_app.area_graph_view import AreaGraphView
            from demo_app.async_demo_view import AsyncDemoView
            self.sub_views = {
                "Area Graph Demo": self.get_view(AreaGraphView),
                "Async Graph Demo": self.get_view(AsyncDemoView),
            }

        return html.Div(
            children=DemoView.raw_render(
                self.watchlist,
                job_def_service.get_by_id(self.test_job_id),
                job_def_service,
                data_tables=self.data_tables,
                tsdp_data_tables=self.tsdp_datatables,
                simple_tsdp_dash=self.simple_tsdp_dash,
                sub_views=self.sub_views
            ),
            id=self.wrapper_div_id
        )
