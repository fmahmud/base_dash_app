from typing import List

from dash import html
import dash_bootstrap_components as dbc


class Alert:
    def __init__(self, body, icon=None, header=None, dismissable=True, duration=None, style=None):
        self.body = body
        self.icon = icon
        self.header = header
        self.dismissable = dismissable
        self.style = style if style is not None else {}
        self.duration = duration


def render_alerts_div(alerts: List[Alert], wrapper_style=None):
    if wrapper_style is None:
        wrapper_style = {}

    if len(alerts) == 0:
        wrapper_style["display"] = "none"

    return html.Div(
        children=[
            dbc.Toast(
                children=alert.body,
                id=f"alert-divs-id-{i}",
                header=alert.header,
                dismissable=alert.dismissable,
                icon=alert.icon,
                style={**{"width": "350px"}, **alert.style},
                duration=alert.duration
            )
            for i, alert in enumerate(alerts)
        ],
        style={
            "position": "absolute", "top": "15px", "right": "15px", "width": "380px", "padding": "15px",
            **wrapper_style
        }
    )