import datetime
import random
import re

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.data_visualization.simple_area_graph import AreaGraph
from base_dash_app.views.base_view import BaseView
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint

RELOAD_GRAPH_BTN_ID = "reload-graph-btn-id"


class AreaGraphView(BaseView):
    def __init__(self, **kwargs):
        super().__init__(
            title="Area Graph View",
            url_regex=re.compile("$a"),
            show_in_navbar=False,
            input_to_states_map=[
                InputToState(
                    input_mapping=InputMapping(
                        input_id=RELOAD_GRAPH_BTN_ID,
                        input_property="n_clicks",
                    ),
                    states=[],
                )
            ],
            **kwargs
        )

        self.area_graph = AreaGraph(title="Area Graph Demo")

    def validate_state_on_trigger(self):
        return

    def handle_any_input(self, *args, triggering_id, index):
        if triggering_id.startswith(RELOAD_GRAPH_BTN_ID):
            self.generate_graph_data()

        return [AreaGraphView.raw_render(self.area_graph)]

    def generate_graph_data(self):
        self.area_graph.series = {}
        self.area_graph.add_series(
                name="Series 1",
                graphables=[
                    TimeSeriesDataPoint(
                        date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                        value=random.randint(0, 100)
                    )
                    for i in range(100)
                ]
            ).add_series(
                name="Series 2",
                graphables=[
                    TimeSeriesDataPoint(
                        date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                        value=random.randint(0, 100) * 1.5
                    )
                    for i in range(100)
                ]
            ).add_series(
                name="Series 3",
                graphables=[
                    TimeSeriesDataPoint(
                        date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                        value=random.randint(0, 100) * 2
                    )
                    for i in range(100)
                ]
            )

    @staticmethod
    def raw_render(area_graph: AreaGraph):
        return html.Div(
            children= [
                dbc.Button("Reload Graph", id=RELOAD_GRAPH_BTN_ID),
                area_graph.render(
                    smoothening=0,
                    height=800,
                    style={"width": "100%", "height": "100%", "padding": "20px"}
                )
            ]
        )

    def render(self, *args, **kwargs):
        self.generate_graph_data()
        return html.Div(
            id=self.wrapper_div_id,
            children=AreaGraphView.raw_render(self.area_graph)
        )