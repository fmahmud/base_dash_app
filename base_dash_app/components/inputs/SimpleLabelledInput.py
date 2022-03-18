from typing import Dict

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.components.base_component import BaseComponent


class SimpleLabelledInput(BaseComponent):
    def __init__(
            self, input_id, label: str = None, placeholder: str = None,
            form_text: str = None, valid_form_feedback: str = None,
            invalid_form_feedback: str = None, style_override: Dict = None,
            initial_validity: bool = None, input_type: str = None
    ):
        self.label = label
        self.input_id = input_id
        self.placeholder = placeholder
        self.form_text = form_text
        self.valid_form_feedback = valid_form_feedback
        self.invalid_form_feedback = invalid_form_feedback
        self.style = {"padding": "10px", "marginBottom": "15px"}
        if style_override is not None:
            self.style = {**self.style, **style_override}

        self.is_valid = initial_validity
        self.input_type = input_type if input_type is not None else "text"

    def render(self, *args, **kwargs):
        return html.Div(
            children=[
                dbc.Label(self.label, html_for=self.input_id) if self.label is not None else None,
                dbc.Input(
                    placeholder=self.placeholder, id=self.input_id,
                    style=self.style, valid=self.is_valid, type=self.input_type
                ),
                dbc.FormText(self.form_text) if self.form_text is not None else None,
                dbc.FormFeedback(self.valid_form_feedback, type="valid")
                if self.valid_form_feedback is not None else None,
                dbc.FormFeedback(self.invalid_form_feedback, type="invalid")
                if self.invalid_form_feedback is not None else None,
            ]
        )
