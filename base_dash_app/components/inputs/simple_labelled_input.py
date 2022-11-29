from typing import Dict

import dash_bootstrap_components as dbc
from dash import html

from base_dash_app.components.base_component import BaseComponent


class SimpleLabelledInput(BaseComponent):
    def __init__(
            self, input_id, label: str = None, placeholder: str = None,
            form_text: str = None, valid_form_feedback: str = None,
            invalid_form_feedback: str = None, style_override: Dict = None,
            initial_validity: bool = None, input_type: str = None,
            required: bool = False, disabled: bool = False, starting_value=None
    ):
        self.label = label
        self.input_id = input_id
        self.placeholder = placeholder
        self.form_text = form_text
        self.valid_form_feedback = valid_form_feedback
        self.invalid_form_feedback = invalid_form_feedback
        self.style = {"padding": "10px"}
        if style_override is not None:
            self.style = {**self.style, **style_override}

        self.required: bool = required
        self.is_valid = initial_validity
        self.input_type = input_type if input_type is not None else "text"
        self.disabled = disabled
        self.starting_value = starting_value

    def render(self, *args, wrapper_style_override=None, **kwargs):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        input_params = {
            "placeholder": self.placeholder,
            "id": self.input_id,
            "style": self.style,
            "type": self.input_type,
            "required": self.required,
            "invalid": self.is_valid is False,
            "disabled": self.disabled,
        }

        if self.is_valid is True:
            input_params["valid"] = True

            if "invalid" in input_params:
                del input_params["invalid"]
        elif self.is_valid is False:
            if "valid" in input_params:
                del input_params["valid"]

            input_params["invalid"] = True
        else:
            if "valid" in input_params:
                del input_params["valid"]

            if "invalid" in input_params:
                del input_params["invalid"]

        if self.starting_value is not None:
            input_params["value"] = self.starting_value

        return html.Div(
            children=[
                dbc.Label(self.label, html_for=self.input_id) if self.label is not None else None,
                dbc.Input(**input_params),
                dbc.FormText(self.form_text) if self.form_text is not None else None,
                dbc.FormFeedback(self.valid_form_feedback, type="valid")
                if self.valid_form_feedback is not None else None,
                dbc.FormFeedback(self.invalid_form_feedback, type="invalid")
                if self.invalid_form_feedback is not None else None,
            ],
            style={"marginTop": "15px", **wrapper_style_override}
        )
