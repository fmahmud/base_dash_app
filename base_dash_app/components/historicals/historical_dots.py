from typing import List

import dash_html_components as html
from dash.development.base_component import Component

from base_dash_app.enums.status_colors import StatusColors
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent, CachedResultableEvent


def __render_event_rectangle(color: StatusColors):
    return html.Span(
        style={
            "height": "20px", "width": "20px", "backgroundColor": color.value,
            "display": "inline-block", "marginRight": "2px", "borderRadius": "30px",
            "verticalAlign": "middle"
        }
    )


def render(data: List[StatusColors] = []) -> Component:
    if len(data) == 0:
        return html.Div()

    dots = [__render_event_rectangle(datum) for datum in data]

    the_div = html.Div(
        children=dots,
        style={"width": "100%", "height": "100%"}
    )

    return the_div


def render_from_resultable_events(data: List[CachedResultableEvent]) -> Component:
    if len(data) == 0:
        return html.Div()

    dots = [__render_event_rectangle(datum.get_status_color()) for datum in data]

    the_div = html.Div(
        children=dots,
        style={"width": "100%", "height": "100%"}
    )

    return the_div
