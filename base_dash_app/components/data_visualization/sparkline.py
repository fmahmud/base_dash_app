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

    def render(self, height=40):

        x_data = []
        y_data = []
        labels = []
        for datum in self.series:
            x_data.append(datum.get_x())
            y_data.append(datum.get_y())
            labels.append(datum.get_label())

        graph = go.Scatter(
            x=x_data, y=y_data, text=labels,  # fill='tozeroy', fillcolor="rgba(76, 17, 48, 0.5)",
            line=Line(color="rgba(76, 17, 48, 1)", width=1)
        )

        layout = {
            "font": {"family": "Georgia, serif"},
            "width": 300,
            'margin': {'l': 0, 'r': 0, 'b': 0, 't': 0},
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            "xaxis": {
                "showticklabels": False,
                "fixedrange": True,
            },
            "yaxis": {
                "showticklabels": False,
                "fixedrange": True,

            },
            "height": height,
            "hovermode": False,
        }

        figure = go.Figure(layout=layout, data=graph)
        if len(y_data) > 0:
            figure.update_yaxes(range=[min(y_data), max(y_data)])
        return dcc.Graph(
            id=self.title.replace(" ", "-"),
            figure=figure,
            config={
                'displayModeBar': False,
            },
            style={"position": "relative", "float": "left", "marginTop": "8px"}
        )