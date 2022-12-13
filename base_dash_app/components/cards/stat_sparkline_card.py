from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.cards.statistic_card import StatisticCard
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.labelled_value_chip import LabelledValueChip, LabelledChipGroup
from base_dash_app.virtual_objects.interfaces.graphable import Graphable
from base_dash_app.virtual_objects.time_series_data_point import TimeSeriesDataPoint


class StatSparklineCard(BaseComponent):
    def __init__(
        self,
        values: List[LabelledValueChip],
        series: List[Graphable],
        title=None,
        unit: str = None,
        graph_height: int = 40,
        shape="spline",
        smoothening=0.8,
    ):
        self.values = values
        self.series = series
        self.title = title
        self.unit = unit
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.height = 138 + self.graph_height

    def render(self, *args, **kwargs):
        info_card = InfoCard()

        sparkline = Sparkline(
            title=self.title, series=self.series
        )

        info_card.add_content(
            sparkline.render(
                width=info_card.width,
                height=self.graph_height,
                wrapper_style_override={
                    "position": "relative",
                    "float": "left",
                    "clear": "left",
                    "marginBottom": "10px",
                    "marginTop": "5px",
                    "width": "calc(100% + 2rem)",
                    "marginLeft": "-1rem"
                },
                shape=self.shape,
                smoothening=self.smoothening
            )
        )

        info_card.add_content(
            html.H4(
                self.title,
                style={
                    "position": "relative", "float": "left", "clear": "left", "width": "100%",
                    "marginTop": "10px", "marginBottom": "10px", "overflow": "hidden", "height": "30px"
                }
            ),
        )

        info_card.add_content(
            LabelledChipGroup(
                values=self.values
            ).render()
        )
        info_card.set_height(self.height)

        return info_card.render()

