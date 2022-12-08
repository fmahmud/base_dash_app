from typing import List

from base_dash_app.components.cards.statistic_card import StatisticCard
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.labelled_value_chip import LabelledValueChip
from base_dash_app.virtual_objects.time_series_data_point import TimeSeriesDataPoint


class StatSparklineCard(StatisticCard):
    def __init__(
        self,
        values: List[LabelledValueChip],
        series: List[TimeSeriesDataPoint],
        title=None,
        unit: str = None,
        graph_height: int = 40,
    ):
        super().__init__(values, title, unit)
        self.height = 160 + graph_height
        self.sparkline = Sparkline(
            title=title, series=series
        )

        self.content.insert(
            0,
            self.sparkline.render(
                width=self.width,
                height=graph_height,
                wrapper_style_override={
                    "position": "relative",
                    "float": "left",
                    "clear": "left",
                    "marginBottom": "10px",
                    "marginTop": "5px",
                    "width": "calc(100% + 2rem)",
                    "marginLeft": "-1rem"
                },
            )
        )
