import dash_bootstrap_components as dbc
from dash import dcc

from dash import html
from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.linkable import Linkable
from base_dash_app.virtual_objects.interfaces.listable import Listable


class SplitListItem(BaseComponent):
    def render(self, listable: Listable):
        header, header_style = listable.get_header()
        text, text_style = listable.get_text()

        extras_list = []
        extras = listable.get_extras()
        left_side_width = "100%"
        right_side_width = "0%"

        if extras is not None:
            extras_list.append(extras)
            left_side_width = "60%"
            right_side_width = "40%"

        link = ""
        if isinstance(listable, Linkable):
            listable: Linkable
            link = listable.get_link()

        return dbc.ListGroupItem(
            dcc.Link(
                children=[
                    html.Div(
                        children=[
                            dbc.ListGroupItemHeading(header, style=header_style),
                            dbc.ListGroupItemText(text, style=text_style),
                        ],
                        style={"position": "absolute", "left": 0, "top": 0, "bottom": 0, "width": left_side_width,
                               "padding": 10}),
                    html.Div(
                        children=extras_list,
                        style={"width": right_side_width, "height": "100%", "position": "absolute",
                               "right": 0, "top": 0, "padding": "17px"}
                    )
                ], href=link
            ),
            style={"height": 100, "background": "rgba(0,0,0,1)", "color": "white"}
        )
