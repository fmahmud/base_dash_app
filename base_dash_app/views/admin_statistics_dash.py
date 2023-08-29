import datetime
import json
import re
from operator import itemgetter

import dash.dcc
from dash import html
from pympler import tracker

from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.cards.statistic_card import StatisticCard
from base_dash_app.components.data_visualization.simple_line_graph import LineGraph, GraphableSeries
from base_dash_app.components.datatable import datatable_wrapper
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.components.labelled_value_chip import LabelledValueChip
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.timeseries.time_series import TimeSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
import dash_bootstrap_components as dbc

STATS_INTERVAL_COMPONENT = 'admin-stats-interval-component'


class AdminStatisticsDash(BaseView):

    def __init__(
        self, memory_timeseries: TimeSeries,
        cpu_timeseries: TimeSeries,
        **kwargs
    ):
        super().__init__(
            "Memory Statistics View",
            re.compile("^/admin/statistics$"),
            show_in_navbar=False,
            nav_url="/admin/statistics",
            input_to_states_map=[
                InputToState(
                    input_mapping=InputMapping(
                        input_id=STATS_INTERVAL_COMPONENT,
                        input_property="n_intervals",
                    ),
                    states=[]
                ),
            ],
            **kwargs,
        )
        self.current_tab_id = 'tab-0'

        self.statistics = {
            "sum": 0,
            "num_objects": 0,
        }

        self.memory_timeseries = memory_timeseries
        self.cpu_timeseries = cpu_timeseries

        def wrapped_reload_function(stats_object):
            def filter_function(m):
                stats_object["sum"] += m[2]
                stats_object["num_objects"] += m[1]
                return m[2] > 50000

            def reload_memory_usages(*args, **kwargs):
                stats_object["sum"] = 0
                stats_object["num_objects"] = 0

                mem = tracker.SummaryTracker()
                memory_usages = list(sorted(mem.create_summary(), reverse=True, key=itemgetter(2)))
                data_to_return = [
                    {'type': x[0], 'num_objects': x[1], 'total_size': x[2] / 1000000}
                    for x in filter(filter_function, memory_usages)
                ]

                return data_to_return

            return reload_memory_usages

        self.memory_dtw = DataTableWrapper(
            columns=[
                {
                    'name': 'Type',
                    'id': 'type',
                },
                {
                    'name': 'Num Objects',
                    'id': 'num_objects',
                    "type": "numeric",
                    "format": datatable_wrapper.integer_format,
                },
                {
                    'name': 'Total Size',
                    'id': 'total_size',
                    "type": "numeric",
                    "format": datatable_wrapper.float_format,
                },
            ],
            reload_data_function=wrapped_reload_function(self.statistics),
            title="Memory Usages",
        )

    def handle_any_input(self, *args, triggering_id, index):
        return [AdminStatisticsDash.raw_render(
            memory_timeseries=self.memory_timeseries,
            cpu_timeseries=self.cpu_timeseries,
            statistics=self.statistics,
            memory_dtw=self.memory_dtw,
            current_tab_id=self.current_tab_id,
        )]

    @staticmethod
    def raw_render(
            memory_timeseries: TimeSeries,
            cpu_timeseries: TimeSeries,
            statistics: dict,
            memory_dtw: DataTableWrapper,
            current_tab_id: str = 'tab-0',
            *args, **kwargs
    ):
        latest_mem_usage = memory_timeseries[-1].get_y() if len(memory_timeseries) > 0 else 0
        return html.Div(
            children=[
                html.Div(
                    children=[
                        dash.dcc.Interval(
                            id=STATS_INTERVAL_COMPONENT,
                            interval=60000,
                            n_intervals=0,
                        ),
                        LineGraph(title="Historic Usage Statistics")
                        .add_graphable_series(memory_timeseries)
                        .add_graphable_series(cpu_timeseries)
                        .render(),
                        # render statistics in stat cards
                        StatisticCard(
                            title="Total Memory Usage",
                            values=[
                                LabelledValueChip(
                                    label="Total Memory Usage",
                                    value=f"{latest_mem_usage:,.2f}",
                                )
                            ],
                            unit="MB"
                        ).render(),
                        StatisticCard(
                            title="Total Number of Objects",
                            values=[
                                LabelledValueChip(
                                    label="Total Number of Objects",
                                    value=f"{statistics['num_objects']:,}",
                                )
                            ],
                        ).render(),
                    ]
                ),
                dbc.Tabs(
                    id="admin-statistics-tabs",
                    active_tab=current_tab_id,
                    children=[
                        dbc.Tab(
                            label="Memory Usage Table",
                            tab_id="tab-0",
                            children=[
                                memory_dtw.render()
                            ]
                        ),
                    ]
                )
            ]
        )

    def render(self, *args, **kwargs):
        return html.Div(
            children=[
                AdminStatisticsDash.raw_render(
                    memory_timeseries=self.memory_timeseries,
                    cpu_timeseries=self.cpu_timeseries,
                    statistics=self.statistics,
                    memory_dtw=self.memory_dtw,
                    current_tab_id=self.current_tab_id,
                )
            ],
            id=self.wrapper_div_id
        )
