import math
from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent


class LabelledValueChip(BaseComponent):
    def __init__(
            self, label, value,
            percent_change=0.0,
            lower_is_better=False,
    ):
        self.label = label
        self.value = value
        self.is_first = False
        self.previous_value = None
        self.percent_change: float = percent_change or 0.0
        self.lower_is_better = lower_is_better

    def set_previous_value(self, current_value, previous_value):
        self.previous_value = previous_value
        # calculate percent change
        if self.previous_value is not None and current_value is not None and self.previous_value != 0:
            self.percent_change = (current_value - self.previous_value) / self.previous_value
            # if self.lower_is_better:
            #     self.percent_change *= -1
        else:
            self.percent_change = 0.0

    def render(self, show_previous_value=False, show_percent_change=False, wrapper_div_style_override=None):
        if wrapper_div_style_override is None:
            wrapper_div_style_override = {}

        return html.Div(
            children=[
                html.Div(
                    f"{'▲' if self.percent_change > 0 else ''}"
                    f"{'▼' if self.percent_change < 0 else ''}"
                    f"{self.percent_change:.1%}",
                    style={
                        "position": "relative", "float": "left", "clear": "left",
                        "color": "red" if self.percent_change < 0 else "green"
                    }
                ) if show_percent_change else None,
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

    def render(
            self, hide_overflow=True, wrapper_style_override=None, max_num_values=6,
            show_percentages=False, show_previous_values=False
    ):
        if wrapper_style_override is None:
            wrapper_style_override = {}

        max_height = 40
        if show_percentages:
            max_height += 20
        if show_previous_values:
            max_height += 20

        return html.Div(
            children=[
                v.render(
                    wrapper_div_style_override={
                        "minWidth": "75px",
                        "width": f"calc({(math.floor(100 / min(len(self.values), max_num_values))):.0f}% - 10px)",
                        "overflow": "hidden" if hide_overflow else "visible"
                    },
                    show_percent_change=show_percentages,
                    show_previous_value=show_previous_values
                ) for v in self.values
            ],
            style={
                "width": "100%", "position": "relative", "float": "left", "overflow": "hidden",
                "maxHeight": f"{max_height}px", **wrapper_style_override
            }
        )