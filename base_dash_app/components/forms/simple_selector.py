from typing import List, Callable

import dash_bootstrap_components as dbc
from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.selectable import Selectable


class SimpleSelector(BaseComponent):
    def __init__(
            self, selectables: List[Selectable],
            comp_id: str, placeholder: str, style=None):
        self.selectables: List[Selectable] = selectables
        self.comp_id: str = comp_id
        self.placeholder: str = placeholder
        self.style = style

    def render(self, *args, **kwargs):
        return render_simple_selector(
            selectables=self.selectables,
            comp_id=self.comp_id,
            placeholder=self.placeholder,
            style=self.style
        )


def render_simple_selector(
        selectables: List[Selectable], comp_id, placeholder, style=None
):
    if style is None:
        style = {"padding": "10px", "marginBottom": "15px"}

    return dbc.Select(
        options=[
            {"label": selectable.get_label(), "value": selectable.get_value()}
            for selectable in selectables
        ],
        id=comp_id,
        placeholder=placeholder,
        style=style
    )