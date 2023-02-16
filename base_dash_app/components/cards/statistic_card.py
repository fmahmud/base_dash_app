from typing import List, Optional

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.labelled_value_chip import LabelledValueChip, LabelledChipGroup


class StatisticCard(BaseComponent):
    def __init__(self, values: List[LabelledValueChip] = None, title=None, unit: str = None):
        super().__init__()
        self.title: Optional[str] = title
        self.unit: Optional[str] = unit
        self.values: List[LabelledValueChip] = values or []

        if len(values) > 0:
            values[0].is_first = True

    def add_value(self, value: LabelledValueChip):
        self.values.append(value)
        return self

    def render(self, style_override=None):
        if style_override is None:
            style_override = {}

        info_card = InfoCard()
        info_card.set_content([
            html.H4(
                self.title,
                style={
                    "position": "relative", "float": "left", "clear": "left", "width": "100%",
                    "marginTop": "10px", "marginBottom": "10px", "overflow": "hidden", "height": "30px"
                }
            ),
            LabelledChipGroup(self.values).render()
        ])

        return info_card.render(style_override=style_override)
