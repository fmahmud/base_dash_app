import datetime
import json
import re
from operator import itemgetter

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
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


class AdminStatisticsDash(BaseView):

    def __init__(self, **kwargs):
        super().__init__(
            "Demo View",
            re.compile("^/admin/statistics$"),
            show_in_navbar=False,
            nav_url="/admin/statistics",
            input_to_states_map=[
                # InputToState(
                #     input_mapping=InputMapping(
                #         input_id=TEST_ALERT_BTN_ID,
                #         input_property="n_clicks"
                #     ),
                #     states=[]
                # ),
                # InputToState(
                #     input_mapping=InputMapping(
                #         input_id=SEARCH_BUTTON_ID,
                #         input_property="n_clicks"
                #     ),
                #     states=[
                #         StateMapping(
                #             state_id=SEARCH_BAR_ID,
                #             state_property="value"
                #         )
                #     ]
                # )
            ],
            **kwargs,
        )
        self.current_tab_id = 'tab-0'

        self.statistics = {
            "sum": 0,
            "num_objects": 0,
        }

        self.historic_stats = []  # list of dicts with keys: type, num_objects, total_size and timestamp

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

                # add timestamp to historic stats
                self.historic_stats.append({
                    "num_objects": stats_object["num_objects"],
                    "total_size": stats_object["sum"],
                    "timestamp": datetime.datetime.now()
                })

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
        pass

    @staticmethod
    def raw_render(*args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        mem = tracker.SummaryTracker()
        return html.Div(
            children=[
                html.Div(
                    children=[
                        #render graph of historic stats
                        LineGraph(
                            title="Historic Usage Statistics",
                        ).add_graphable_series(
                            GraphableSeries(
                                name="Total Memory Usage",
                                data=[
                                    TimeSeriesDataPoint(
                                        date=x["timestamp"],
                                        value=x["total_size"] / 1000000,
                                    )
                                    for x in self.historic_stats
                                ]
                            )
                        ).add_graphable_series(
                            GraphableSeries(
                                name="Total Num Objects",
                                data=[
                                    TimeSeriesDataPoint(
                                        date=x["timestamp"],
                                        value=x["num_objects"],
                                    )
                                    for x in self.historic_stats
                                ],
                                secondary_y=True
                            )
                        ).render(),
                        # render statistics in stat cards
                        StatisticCard(
                            title="Total Memory Usage",
                            values=[
                                LabelledValueChip(
                                    label="Total Memory Usage",
                                    value=f"{self.statistics['sum'] / 1000000:,.2f}",
                                )
                            ],
                            unit="MB"
                        ).render(),
                        StatisticCard(
                            title="Total Number of Objects",
                            values=[
                                LabelledValueChip(
                                    label="Total Number of Objects",
                                    value=f"{self.statistics['num_objects']:,}",
                                )
                            ],
                        ).render(),
                    ]
                ),
                self.memory_dtw.render(),
            ]
        )
