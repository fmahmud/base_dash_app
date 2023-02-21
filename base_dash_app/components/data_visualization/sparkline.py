from dash import html

from base_dash_app.components.base_component import BaseComponent
import plotly.graph_objects as go
from plotly.graph_objs.scatter import Line
import dash_core_components as dcc
from typing import List
from base_dash_app.virtual_objects.interfaces.graphable import Graphable


class Sparkline(BaseComponent):
    def __init__(self, title: str, series: List[Graphable]):
        self.title: str = title
        self.series: List[Graphable] = series

    def render(
            self, height=40, width=300, shape="spline", smoothening=0.8, wrapper_style_override=None,
            mouse_interactions=False, show_x_axis=False, show_y_axis=False, show_custom_x_axis=True
    ):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        x_data = []
        y_data = []
        labels = []
        for datum in self.series:
            x_data.append(datum.get_x())
            y_data.append(datum.get_y())
            labels.append(datum.get_label())
        xmin = min(x_data, default=0)
        xmax = max(x_data, default=0)

        ymin = round(min(y_data, default=0), 2)
        ymax = round(max(y_data, default=0), 2)

        graph = go.Scatter(
            x=x_data, y=y_data, text=labels,  # fill='tozeroy', fillcolor="rgba(76, 17, 48, 0.5)",
            line=Line(color="rgba(0, 0, 0, 1)", width=2, shape=shape, smoothing=smoothening),
            mode="lines"
        )

        layout = {
            "font": {"family": "Georgia, serif"},
            "width": width,
            'margin': {'l': 0, 'r': 0, 'b': 1, 't': 1},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            "xaxis": {
                "visible": show_x_axis,
                "showticklabels": show_x_axis,
                "fixedrange": True,
            },
            "yaxis": {
                "visible": show_y_axis,
                "showticklabels": show_y_axis,
                "fixedrange": True,

            },
            "showlegend": False,
            "height": height - 12,
            "hovermode": "x" if mouse_interactions else False,
        }

        figure = go.Figure(layout=layout, data=graph)
        if len(y_data) > 0:
            figure.update_yaxes(range=[ymin - abs(ymax * 0.1), ymax + abs(ymax * 0.1)])

        return html.Div(
            children=[
                dcc.Graph(
                    id=self.title.replace(" ", "-"),
                    figure=figure,
                    config={
                        'displayModeBar': not mouse_interactions,
                        'staticPlot': not mouse_interactions
                    },
                ),
                html.Div(
                    children=[
                        html.Div(
                            xmin.strftime("%Y-%m-%d"), style={"position": "relative", "float": "left"}
                        ) if len(y_data) > 0 else None,
                        html.Div(
                            xmax.strftime("%Y-%m-%d"), style={"position": "relative", "float": "right"}
                        ) if len(y_data) > 0 else None
                    ],
                    style={
                        "width": "calc(100% - 32px)", "height": "12px", "position": "relative", "float": "left",
                        "fontSize": "12px", "marginTop": "2px", "marginLeft": "16px"
                    }
                ) if show_custom_x_axis else None
            ],
            style={"position": "relative", "float": "left", "marginTop": "8px", **wrapper_style_override}
        )