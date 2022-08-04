from typing import List
import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.virtual_objects.interfaces.listable import Listable


def render_list_card(
        listables: List[Listable],
        title: str,
        buttons: List = None,
        style=None
):
    if buttons is None:
        buttons = []

    if style is None:
        style = {}

    return dbc.Card(
        children=[
            dbc.CardHeader(html.H4(title)),
            dbc.ListGroup([
                dbc.ListGroupItem(
                    children=[
                        html.Div(listable.get_header()[0], style=listable.get_header()[1]),
                        html.Div(listable.get_text()[0], style=listable.get_text()[1])
                    ]
                )
                for listable in listables
            ], flush=True),
            dbc.CardFooter(
                dbc.ButtonGroup(buttons) if len(buttons) > 0 else None,
            )
        ],
        style={
            "width": "30%", "position": "relative", "float": "left",
            "margin": "20px", "minWidth": "300px", **style
        },
    )