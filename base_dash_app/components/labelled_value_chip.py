from typing import List

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


class LabelledChipGroup(BaseComponent):
    def __init__(self, values: List[LabelledValueChip]):
        self.values = values
        if len(self.values) > 0:
            self.values[0].is_first = True

    def render(self, hide_overflow=True):
        return html.Div(
            children=[
                v.render({
                    "minWidth": "75px",
                    "width": f"calc({(100 / len(self.values)):.0f}% - 10px)",
                    "overflow": "hidden" if hide_overflow else "visible"
                }) for v in self.values
            ],
            style={
                "width": "100%", "position": "relative", "float": "left", "overflow": "hidden",
                "maxHeight": "40px"
            }
        )