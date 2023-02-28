from typing import List, Dict
import dash_core_components as dcc
import plotly.graph_objects as go
from plotly.graph_objs.scatter import Line

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.graphable import Graphable


class AreaGraph(BaseComponent):
    def __init__(self, title: str = ""):
        self.title: str = title
        self.series: Dict[str, List[Graphable]] = {}

    def add_series(
            self, name, graphables: List[Graphable]
    ):
        self.series[name] = graphables
        return self

    def render(
        self,
        smoothening=0.8,
        height=500,
        show_legend=False,
        style=None
    ):
        if style is None:
            style = {}

        scatters = []
        for k, v in self.series.items():
            X = []
            Y = []
            for g in v:
                X.append(g.get_x())
                Y.append(g.get_y())

            scatters.append(
                go.Scatter(
                    x=X, y=Y, name=k, line=Line(width=2),
                    mode="lines", stackgroup="one"
                )
            )

        figure = go.Figure(
            data=scatters,
            layout={
                'yaxis': {'type': 'linear', 'fixedrange': True},
                'xaxis': {'showgrid': False, 'fixedrange': False},
                'margin': {'l': 30, 'r': 10, 'b': 30, 't': 40},
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'plot_bgcolor': 'rgba(0,0,0,0)',
                "hovermode": "x",
                "showlegend": show_legend,
                "height": height,
            },

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

        return dcc.Graph(
            id=self.title.replace(" ", "-"),
            figure=figure,
            config={
                'displayModeBar': False,
                # 'hovermode': 'x',
            },
            style={"width": "50%", "position": "relative", "float": "left", **style}
        )

