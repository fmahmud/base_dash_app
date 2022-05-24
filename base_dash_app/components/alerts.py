import json
from typing import List

from dash import html
import dash_bootstrap_components as dbc

CLEAR_ALL_ALERTS_BTN_ID = "clear-all-alerts-btn-id"

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

    def __eq__(self, other):
        if type(other) == type(self):
            return other.id == self.id

        return False

    def __hash__(self):
        return hash(self.id)


def render_alerts_div(alerts: List[Alert], wrapper_style=None):
    if wrapper_style is None:
        wrapper_style = {}

    if len(alerts) == 0:
        wrapper_style["display"] = "none"

    alert_comps = [
        dbc.Alert(
            children=[
                html.Div(
                    alert.body,
                    style={
                        "position": "relative", "float": "left", "maxWidth": "calc(100% - 40px)",
                        "overflow": "hidden", "whiteSpace": "nowrap", "textOverflow": "ellipsis"
                    }
                ),
                html.Button(
                    className="btn-close", type="button", id={"type": DISMISS_ALERT_BTN_ID, "index": alert.id},
                    style={"position": "absolute", "right": "14px", "top": "14px"}
                ),
            ],
            is_open=True,
            style={**{"width": "550px", "position": "relative", "float": "right"}, **alert.style},
            color=alert.color
        )
        for alert in alerts
    ]

    clear_all_button = dbc.Badge(
        "Clear All",
        href="#",
        color="dark",
        className="me-1 text-decoration-none",
        pill=True,
        id=CLEAR_ALL_ALERTS_BTN_ID,
        style={
            "position": "relative",
            "float": "left",
            "marginTop": "-8px",
            "marginBottom": "10px",
            "height": "30px",
            "width": "65px",
            "lineHeight": "25px",
            "zIndex": "1000",
            "display": "none" if len(alert_comps) < 3 else "inherit",
        }
    )

    return html.Div(
        children=[
            clear_all_button,
            *alert_comps
        ],
        style={
            "position": "relative", "padding": "15px", "pointerEvents": "auto", **wrapper_style
        }
    )