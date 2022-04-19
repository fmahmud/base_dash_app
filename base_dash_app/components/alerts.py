import json
from typing import List

from dash import html
import dash_bootstrap_components as dbc

DISMISS_ALERT_BTN_ID = "close-alert-btn-id"

num_alerts = 0


class Alert:
    def __init__(self, body, icon=None, header=None, dismissable=True, duration=None, style=None, color="secondary"):
        self.body = body
        self.icon = icon
        self.header = header
        self.dismissable = dismissable
        self.style = style if style is not None else {}
        self.duration = duration
        global num_alerts
        num_alerts += 1
        self.id = num_alerts
        self.color = color

    @staticmethod
    def from_dict(dictionary):
        return Alert(**dictionary)

    @staticmethod
    def from_json_string(string_repr):
        return Alert.from_dict(json.loads(string_repr))

    def to_json_string(self):
        return json.dumps(vars(self))


def render_alerts_div(alerts: List[Alert], wrapper_style=None):
    if wrapper_style is None:
        wrapper_style = {}

    if len(alerts) == 0:
        wrapper_style["display"] = "none"

    return html.Div(
        children=[
            dbc.Alert(
                children=[
                    alert.body,
                    html.Button(
                        className="btn-close", type="button", id={"type": DISMISS_ALERT_BTN_ID, "index": alert.id},
                        style={"position": "relative", "float": "right"}
                    ),
                ],
                is_open=True,
                style={**{"width": "550px"}, **alert.style},
                color=alert.color
            )
            for alert in alerts
        ],
        style={
            "position": "absolute", "top": "0px", "right": "0px", "bottom": 0, "left": 0, "padding": "15px",
            "pointerEvents": "auto", **wrapper_style
        }
    )