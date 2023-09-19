from typing import List, Callable

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.selectable import Selectable


class SimpleSelector(BaseComponent):
    def __init__(
            self, selectables: List[Selectable], comp_id,
            placeholder: str, style=None, disabled=False,
            currently_selected_value=None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.selectables: List[Selectable] = selectables
        self.comp_id = comp_id
        self.placeholder: str = placeholder
        self.style = style
        self.disabled: bool = disabled
        self.currently_selected_value = currently_selected_value if currently_selected_value is not None else ''

    def render(self, is_valid=True, error_form_feedback=None, *args, **kwargs):
        return render_simple_selector(
            selectables=self.selectables,
            comp_id=self.comp_id,
            placeholder=self.placeholder,
            style=self.style,
            currently_selected_value=self.currently_selected_value,
            disabled=self.disabled,
            error_form_feedback=error_form_feedback,
            is_valid=is_valid
        )


def render_simple_selector(
        selectables: List[Selectable],
        comp_id, placeholder,
        style=None, currently_selected_value='',
        disabled=False,
        error_form_feedback=None,
        is_valid=True
):
    if style is None:
        style = {"padding": "10px", "marginBottom": "15px"}

    return html.Div(
        children=[
            dbc.Select(
                options=[
                    {"label": selectable.get_label(), "value": selectable.get_value()}
                    for selectable in selectables
                ],
                id=comp_id,
                placeholder=placeholder,
                style=style,
                value=currently_selected_value,
                disabled=disabled,
                invalid=not is_valid,
            ),
            dbc.FormFeedback(
                error_form_feedback or '',
                type="invalid",
            )
        ]
    )