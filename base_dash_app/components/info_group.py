from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
import dash_bootstrap_components as dbc

card_style = {"marginBottom": "10px", "width": "49%", "float": "left", "position": "relative",
              "marginRight": "10px"}


class InfoItemsGroup(BaseComponent):
    def __init__(self):
        self.items = []
        self.title = None

    def add_item(self, item):
        self.items.append(item)
        return self

    def add_items(self, items):
        self.items += items
        return self

    def set_title(self, title):
        self.title = title
        return self

    def render(self, *args, card_style_override=None, wrapper_style_override=None):
        if card_style_override is None:
            card_style_override = {}

        if wrapper_style_override is None:
            wrapper_style_override = {}

        components = []
        if self.title is not None:
            components.append(html.H2(self.title, style={"marginBottom": "10px"}))

        for item in self.items:
            components.append(dbc.Card(item, body=True, style={**card_style, **card_style_override}))

        return html.Div(
            children=components, style=wrapper_style_override
        )
