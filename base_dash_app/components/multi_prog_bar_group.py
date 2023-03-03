from typing import List

from base_dash_app.components.base_component import BaseComponent
from dash import html
import dash_bootstrap_components as dbc


class DetailedProgressBar(BaseComponent):
    def __init__(
            self, title: str, progress: float,
            progress_label: str = None, status_message: str = "",
            color: str = "black", animated: bool = False, striped: bool = False
    ):
        self.title = title
        self.progress = progress
        self.progress_label = progress_label or f"{progress:.0f}%"
        self.status_message = status_message
        self.color = color
        self.animated = animated
        self.striped = striped

    def render(self, *args, **kwargs):
        return html.Div(
            children=[
                html.H4(self.title, style={"float": "left"}),
                html.Pre(self.status_message,
                    style={
                        "position": "relative",
                        "float": "right",
                        "marginBottom": "0px",
                    },
                ) if self.status_message else None,
                dbc.Progress(
                    value=self.progress,
                    label=self.progress_label,
                    color=self.color,
                    animated=self.animated,
                    striped=self.striped,
                    style={
                        "position": "relative",
                        "float": "right",
                        "width": "100%",
                    },
                ),
            ],
            style={
                "position": "relative",
                "float": "left",
                "width": "100%",
                "height": "50px",
                "marginBottom": "20px",
            },
        )


class MultiProgBarGroup(BaseComponent):
    def __init__(self, detailed_prog_bars: List[DetailedProgressBar] = None):
        self.detailed_prog_bars = detailed_prog_bars or []

    def add_detailed_prog_bar(self, detailed_prog_bar: DetailedProgressBar):
        if detailed_prog_bar:
            self.detailed_prog_bars.append(detailed_prog_bar)

    def render(self):
        return html.Div(
            children=[
                detailed_prog_bar.render()
                for detailed_prog_bar in self.detailed_prog_bars
            ],
            style={
                "width": "100%", "height": "100%",
                "display": "fixed",
            },
        )
