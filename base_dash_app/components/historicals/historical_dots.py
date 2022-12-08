from typing import List

from dash import html
from dash.development.base_component import Component

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent, CachedResultableEvent
import dash_bootstrap_components as dbc


def render_event_rectangle(color: StatusesEnum, *, dot_style_override=None, tooltip_id=None):
    if dot_style_override is None:
        dot_style_override = {}

    dot_style = {
        "height": "20px", "width": "20px", "backgroundColor": color.value.hex_color,
        "display": "inline-block", "marginRight": "2px", "borderRadius": "30px",
        "verticalAlign": "middle", **dot_style_override
    }

    if tooltip_id is not None:
        span = html.Span(
            style=dot_style,
            id=tooltip_id
        )
    else:
        span = html.Span(
            style=dot_style,
        )
    return span


def render(data: List[StatusesEnum] = []) -> Component:
    if len(data) == 0:
        return html.Div()

    dots = [render_event_rectangle(datum) for datum in data]

    the_div = html.Div(
        children=dots,
        style={"width": "100%", "height": "100%"}
    )

    return the_div


def render_from_resultable_events(data: List[CachedResultableEvent], *, dot_style_override=None, use_tooltips=False) -> Component:
    if len(data) == 0:
        return html.Div()

    if use_tooltips:
        tooltips = []
        dots = []
        for datum in data:
            dots.append(
                datum.get_event_dot(style_override=dot_style_override)
            )

            tooltips.append(dbc.Tooltip(datum.get_name(), target=datum.get_tooltip_id(), placement="bottom"))

        dots = [*dots, *tooltips]
    else:
        dots = [
            datum.get_event_dot(style_override=dot_style_override)
            for datum in data
        ]

    the_div = html.Div(
        children=dots,
        style={"width": "100%", "height": "100%"}
    )

    return the_div
