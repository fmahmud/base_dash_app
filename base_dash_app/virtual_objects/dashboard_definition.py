import datetime
from abc import ABC
from typing import Optional, List, Dict

from base_dash_app.components.base_component import BaseComponent, ComponentWithInternalCallback

from typing import List

import dash_bootstrap_components as dbc
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.datatable.download_and_reload_bg import construct_down_ref_btgrp
from base_dash_app.virtual_objects.statistics.statistic import Statistic
from base_dash_app.virtual_objects.time_series_data_point import TimeSeriesDataPoint
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


class InfoCard:
    """
    A card that can render any amount of content in the body.
    """

    def __init__(self):
        self.width: int = 400
        self.height: int = 200
        self.content = []

    def set_content(self, content):
        self.content = content
        return self

    def add_content(self, value):
        self.content.append(value)
        return self

    def set_height(self, height):
        self.height = height
        return self

    def set_width(self, width):
        self.width = width
        return self

    def render(self, style_override=None):
        if style_override is None:
            style_override = {}

        return dbc.Card(
            children=dbc.CardBody(
                children=self.content
            ),
            style={
                "position": "relative",
                "float": "left",
                "width": f"{self.width}px",
                "marginRight": "10px",
                "marginBottom": "10px",
                "height": f"{self.height}px",
                "padding": "0px",
                **style_override,
            },
        )


class GraphCard:
    def __init__(self):
        pass


class LabelledValueDiv(BaseComponent):
    def __init__(self, label, value):
        self.label = label
        self.value = value
        self.is_first = False

    def render(self, wrapper_div_style_override=None):
        if wrapper_div_style_override is None:
            wrapper_div_style_override = {}

        return html.Div(
            children=[
                html.Div(
                    self.value,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left"
                    }
                ),
                html.Div(
                    self.label,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left",
                        "fontSize": "10px"
                    }
                )
            ],
            style={
                "position": "relative",
                "float": "left",
                "borderLeft": "1px solid #888" if not self.is_first else "none",
                "paddingLeft": "10px" if not self.is_first else "none",
                "marginLeft": "10px" if not self.is_first else "none",
                **wrapper_div_style_override,
            },
        )


class StatisticCard(InfoCard):
    def __init__(self, values: List[LabelledValueDiv] = None, title=None, unit: str = None):
        super().__init__()
        self.title: Optional[str] = title
        self.unit: Optional[str] = unit
        self.values: List[LabelledValueDiv] = values or []
        self.height = 130

        if len(values) > 0:
            values[0].is_first = True

        self.set_content([
            html.H4(
                title,
                style={
                    "position": "relative", "float": "left", "clear": "left", "width": "100%",
                    "marginTop": "10px", "marginBottom": "10px"
                }
            ),
            html.Div(
                children=[
                    v.render({
                        "minWidth": "75px",
                        "width": f"calc({(100 / len(self.values)):.0f}% - 10px)",
                        "overflow": "hidden"
                    }) for v in self.values],
                style={
                    "width": "100%", "position": "relative", "float": "left", "overflow": "hidden",
                    "maxHeight": "40px"
                }
            )
        ])

    def add_value(self, value: LabelledValueDiv):
        self.values.append(value)
        return self


class StatCardWithSparkline(StatisticCard):
    def __init__(
        self,
        values: List[LabelledValueDiv],
        series: List[TimeSeriesDataPoint],
        title=None,
        unit: str = None,
        graph_height: int = 40,
    ):
        super().__init__(values, title, unit)
        self.height = 160 + graph_height
        self.sparkline = Sparkline(
            title=title, series=series
        )

        self.content.insert(
            0,
            self.sparkline.render(
                width=self.width,
                height=graph_height,
                wrapper_style_override={
                    "position": "relative",
                    "float": "left",
                    "clear": "left",
                    "marginBottom": "10px",
                    "marginTop": "5px",
                    "width": "calc(100% + 2rem)",
                    "marginLeft": "-1rem"
                },
            )
        )


class DashboardLevelGraph:
    pass


class TabLevelGraph:
    pass
