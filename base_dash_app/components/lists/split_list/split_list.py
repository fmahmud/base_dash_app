from typing import List


import dash_bootstrap_components as dbc
from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.lists.split_list.split_list_item import SplitListItem
from base_dash_app.virtual_objects.interfaces.listable import Listable


class SplitList(BaseComponent):
    def __init__(self, title: str = "", style={"display": "block"}):
        self.title = title
        self.style = style

    def render(self, listables: List[Listable], empty_text="There's nothing here"):
        components = []
        if self.title is not None and self.title != "":
            components.append(dbc.ListGroupItem(dbc.ListGroupItemHeading(self.title)))

        for listable in listables:
            components.append(SplitListItem().render(listable))

        if len(listables) == 0:
            components.append(
                dbc.ListGroupItem(empty_text, style={"height": 75, "background": "rgba(0,0,0,1)", "color": "white"})
            )

        return dbc.ListGroup(children=components, style=self.style)
