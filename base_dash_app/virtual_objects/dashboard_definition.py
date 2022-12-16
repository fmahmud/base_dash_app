from abc import ABC
from typing import Optional

from typing import List

import dash_bootstrap_components as dbc

from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from dash import html


def __make_stat_card(
        title,
        value,
        style=None,
        color=None,
        spark_line_data: List[TimeSeriesDataPoint] = None,
        value2=None,
        value3=None,
        value4=None,
        pixel_width: int = 400,
):
    if style is None:
        style = {}

    if spark_line_data is None:
        spark_line_data = []

    kwargs = {}
    if color is not None:
        kwargs["color"] = color

    return dbc.Card(
        children=dbc.CardBody(
            children=[
                Sparkline(title=title, series=spark_line_data).render(
                    width=pixel_width - 32,
                    wrapper_style_override={
                        "position": "relative",
                        "float": "left",
                        "clear": "left",
                        "marginBottom": "10px",
                        "marginTop": "0px",
                    },
                )
                if len(spark_line_data) > 0
                else None,

                html.Div(value, style={"position": "relative", "float": "left", "clear": "left"}),
                html.Div(
                    value2,
                    style={
                        "position": "relative",
                        "float": "left",
                        "borderLeft": "1px solid grey",
                        "paddingLeft": "10px",
                    },
                )
                if value2 is not None
                else None,
                html.Div(
                    value3,
                    style={
                        "position": "relative",
                        "float": "left",
                        "borderLeft": "1px solid grey",
                        "paddingLeft": "10px",
                    },
                )
                if value3 is not None
                else None,
            ]
        ),
        style={
            "position": "relative",
            "float": "left",
            "width": f"{pixel_width}px",
            "marginRight": "10px",
            "marginBottom": "10px",
            "height": "150px",
            "padding": "0px",
            **style,
        },
        **kwargs,
    )


class DashboardDefinition(ABC):
    def __init__(self):
        self.name: Optional[str] = None
        self.author: Optional[str] = None

        self.tabs: List[TabDefinition] = []


class TabDefinition(ABC):
    def __init__(self):
        self.title: Optional[str] = None


class GraphCard:
    def __init__(self):
        pass


class DashboardLevelGraph:
    pass


class TabLevelGraph:
    pass
