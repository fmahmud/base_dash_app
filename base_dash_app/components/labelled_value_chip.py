from dash import html

from base_dash_app.components.base_component import BaseComponent


class LabelledValueChip(BaseComponent):
    def __init__(self, label, value):
        self.label = label
        self.value = value
        self.is_first = False

    def render(self, wrapper_div_style_override=None):
        if wrapper_div_style_override is None:
            wrapper_div_style_override = {}

        return html.Div(
            children=[
                html.Div(
                    self.value,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left"
                    }
                ),
                html.Div(
                    self.label,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left",
                        "fontSize": "10px"
                    }
                )
            ],
            style={
                "position": "relative",
                "float": "left",
                "borderLeft": "1px solid #888" if not self.is_first else "none",
                "paddingLeft": "10px" if not self.is_first else "none",
                "marginLeft": "10px" if not self.is_first else "none",
                **wrapper_div_style_override,
            },
        )
