from enum import Enum
from typing import List, Dict
import plotly.graph_objects as go
from plotly.graph_objs.scatter import Line
from plotly.subplots import make_subplots
from dash import dcc

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.graphable import Graphable
from base_dash_app.virtual_objects.interfaces.nameable import Nameable


class GraphTypes(Enum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    AREA = "area"


class GraphableSeries(Nameable):
    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        if type(item) != int:
            raise TypeError(f"Must be an int, got val={item} type=({type(item)}) instead.")
        return self.data[item]

    def __setitem__(self, key, value):
        if type(key) != int:
            raise TypeError(f"Must be an int, got val={key} type=({type(key)}) instead.")

        if not isinstance(value, Graphable):
            raise TypeError(f"Must be an instance of Graphable, got val={value} type=({type(value)}) instead.")

        self.data[key] = value

    def get_name(self):
        return self.name

    def __init__(
        self,
        name: str = None,
        data: List[Graphable] = None,
        graph_type: GraphTypes = GraphTypes.LINE,
        color: str = None,
        secondary_y: bool = False,
    ):
        self.name: str = name or ""
        self.data: List[Graphable] = data or []
        self.graph_type: GraphTypes = graph_type
        self.color: str = color
        self.secondary_y: bool = secondary_y

    def max_y(self):
        if len(self.data) == 0:
            return 0
        return max([datum.get_y() for datum in self.data])

    def min_y(self):
        if len(self.data) == 0:
            return 0
        return min([datum.get_y() for datum in self.data])

    def get_xs_and_ys(self):
        return [datum.get_x() for datum in self.data], [datum.get_y() for datum in self.data]

    def get_trace(self, shape, smoothening, width=2):
        X, Y = self.get_xs_and_ys()
        if self.graph_type == GraphTypes.LINE:
            return go.Scatter(
                x=X, y=Y, name=self.name,
                line=Line(shape=shape, smoothing=smoothening, width=width),
                mode="lines",
            )
        elif self.graph_type == GraphTypes.BAR:
            return go.Bar(
                x=X, y=Y, name=self.name, marker_color=self.color
            )
        elif self.graph_type == GraphTypes.SCATTER:
            return go.Scatter(
                x=X, y=Y, name=self.name,
                mode="markers"
            )
        elif self.graph_type == GraphTypes.AREA:
            return go.Scatter(
                x=X, y=Y, name=self.name,
                mode="lines",
                stackgroup="one"
            )
        else:
            raise Exception(f"Unknown graph type {self.graph_type}")


class LineGraph(BaseComponent):
    def __init__(self, title: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title: str = title
        self.graphable_series: List[GraphableSeries] = []
        self.barmode = "group"
        self.shape = None
        self.smoothening = None
        self.height = None
        self.show_legend = None
        self.align_y_axes = None

    def add_series(
            self, name, graphables: List[Graphable],
            secondary_y: bool = False, graph_type: GraphTypes = GraphTypes.LINE,
            color: str = None
    ):
        self.graphable_series.append(
            GraphableSeries(
                name=name, data=graphables, secondary_y=secondary_y, graph_type=graph_type, color=color
            )
        )
        return self

    def add_graphable_series(
            self, graphable_series: GraphableSeries,
    ):
        self.graphable_series.append(graphable_series)
        return self

    def render(
        self,
        *,
        shape="spline",
        smoothening=0.8,
        height=500,
        show_legend=False,
        align_y_axes=True,
        style=None,
        show_title=False
    ):
        if style is None:
            style = {}

        include_secondary_y = any(x for x in self.graphable_series if x.secondary_y)
        figure = make_subplots(
            specs=[[{"secondary_y": include_secondary_y}]],
        )

        figure.update_layout(
            **{
                'yaxis': {'type': 'linear', 'fixedrange': True},
                'xaxis': {'showgrid': False, 'fixedrange': False},
                'margin': {'l': 30, 'r': 10, 'b': 30, 't': 40},
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'plot_bgcolor': 'rgba(0,0,0,0)',
                "hovermode": "x",
                "showlegend": self.show_legend or show_legend,
                "height": self.height or height,
                "barmode": self.barmode,
            }
        )

        if show_title:
            figure.update_layout(
                title=self.title or "",
                margin={'l': 30, 'r': 10, 'b': 30, 't': 120},
            )

        for g_series in self.graphable_series:
            figure.add_trace(
                g_series.get_trace(shape=self.shape or shape, smoothening=self.smoothening or smoothening),
                secondary_y=g_series.secondary_y
            )

        figure.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        if include_secondary_y and align_y_axes and len(self.graphable_series) > 1:
            primary_y_max = max([x.max_y() for x in self.graphable_series if not x.secondary_y])
            secondary_y_max = max([x.max_y() for x in self.graphable_series if x.secondary_y])
            primary_y_min = min([x.min_y() for x in self.graphable_series if not x.secondary_y])
            secondary_y_min = min([x.min_y() for x in self.graphable_series if x.secondary_y])

            # primary side
            primary_range = primary_y_max - primary_y_min
            if primary_y_max == 0 == primary_y_min:
                primary_range_ratio = 1
            else:
                primary_range_ratio = primary_range / max(abs(primary_y_max), abs(primary_y_min))

            # secondary side
            secondary_range = secondary_y_max - secondary_y_min
            if secondary_y_max == 0 == secondary_y_min:
                secondary_range_ratio = 1
            else:
                secondary_range_ratio = secondary_range / max(abs(secondary_y_max), abs(secondary_y_min))

            if primary_range_ratio > secondary_range_ratio:
                # use primary range to determine secondary range
                if abs(secondary_y_max) > abs(secondary_y_min):
                    # secondary bigger above zero, need to calculate secondary min
                    secondary_y_min = (primary_y_min / primary_y_max) * secondary_y_max
                else:
                    # secondary bigger below zero, need to calculate secondary max
                    secondary_y_max = (primary_y_max / primary_y_min) * secondary_y_min
            elif primary_range_ratio < secondary_range_ratio:
                # use secondary range to determine primary range
                if abs(primary_y_max) > abs(primary_y_min):
                    # primary bigger above zero, need to calculate primary min
                    primary_y_min = (secondary_y_min / secondary_y_max) * primary_y_max
                else:
                    # primary bigger below zero, need to calculate primary max
                    primary_y_max = (secondary_y_max / secondary_y_min) * primary_y_min

            figure.update_yaxes(
                range=[primary_y_min - abs(primary_y_min) * 0.05, primary_y_max + abs(primary_y_max) * 0.05],
                secondary_y=False
            )

            figure.update_yaxes(
                range=[secondary_y_min - abs(secondary_y_min) * 0.05, secondary_y_max + abs(secondary_y_max) * 0.05],
                secondary_y=True
            )

        return dcc.Graph(
            id=self.title.replace(" ", "-"),
            figure=figure,
            config={
                'displayModeBar': False,
                # 'hovermode': 'x',
            },
            style={"width": "50%", "position": "relative", "float": "left", **style}
        )

