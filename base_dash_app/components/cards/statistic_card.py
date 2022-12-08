from typing import List, Optional

from dash import html

from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.labelled_value_chip import LabelledValueChip


class StatisticCard(InfoCard):
    def __init__(self, values: List[LabelledValueChip] = None, title=None, unit: str = None):
        super().__init__()
        self.title: Optional[str] = title
        self.unit: Optional[str] = unit
        self.values: List[LabelledValueChip] = values or []
        self.height = 130

        if len(values) > 0:
            values[0].is_first = True

        self.set_content([
            html.H4(
                title,
                style={
                    "position": "relative", "float": "left", "clear": "left", "width": "100%",
                    "marginTop": "10px", "marginBottom": "10px"
                }
            ),
            html.Div(
                children=[
                    v.render({
                        "minWidth": "75px",
                        "width": f"calc({(100 / len(self.values)):.0f}% - 10px)",
                        "overflow": "hidden"
                    }) for v in self.values],
                style={
                    "width": "100%", "position": "relative", "float": "left", "overflow": "hidden",
                    "maxHeight": "40px"
                }
            )
        ])

    def add_value(self, value: LabelledValueChip):
        self.values.append(value)
        return self
