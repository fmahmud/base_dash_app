import datetime
from enum import Enum
from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.labelled_value_chip import LabelledChipGroup, LabelledValueChip
from base_dash_app.virtual_objects.time_series_data_point import TimeSeriesDataPoint


class TsdpAggregationFuncs(Enum):
    MEAN = lambda list_of_tsdps: sum([x.value for x in list_of_tsdps]) / len(list_of_tsdps)
    MODE = 2 # todo
    MEDIAN = lambda list_of_tsdps: (sorted(list_of_tsdps, key=lambda t: t.value)[len(list_of_tsdps) // 2]) if len(list_of_tsdps) > 0 else None
    SUM = lambda list_of_tsdps: sum([x.value for x in list_of_tsdps])
    MIN = lambda list_of_tsdps: min([x.value for x in list_of_tsdps])
    MAX = lambda list_of_tsdps: max([x.value for x in list_of_tsdps])
    COUNT = lambda list_of_tsdps: len(list_of_tsdps)
    LATEST_VALUE = lambda list_of_tsdps: sorted(list_of_tsdps)[-1].value if len(list_of_tsdps) > 0 else None
    SEGMENT_START = lambda list_of_tsdps: sorted(list_of_tsdps)[0].value if len(list_of_tsdps) > 0 else None


class TimePeriodsEnum(Enum):
    LATEST = "Latest"
    LAST_HOUR = "Last Hour"
    LAST_24HRS = "Last 24 Hours"
    LAST_7_DAYS = "Last 7 Days"
    LAST_30_DAYS = "Last 30 Days"
    LAST_90_DAYS = "Last 90 Days"
    LAST_365_DAYS = "Last 365 Days"

    ALL_TIME = "All Time"


class TsdpSparklineStatCard(BaseComponent):
    def __init__(
        self,
        series: List[TimeSeriesDataPoint],
        title=None,
        unit: str = None,
        graph_height: int = 40,
        shape="spline",
        smoothening=0.8,
        time_periods_to_show: List[TimePeriodsEnum] = None,
        aggregation_to_use: TsdpAggregationFuncs = TsdpAggregationFuncs.SUM
    ):
        self.series = sorted(series)
        self.title = title
        self.unit = unit
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.height = 138 + self.graph_height
        self.time_periods_to_show: List[TimePeriodsEnum] = time_periods_to_show or [TimePeriodsEnum.LAST_24HRS]
        self.aggregation_to_use: TsdpAggregationFuncs = aggregation_to_use

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

        current_time = datetime.datetime.now()
        values = []
        for time_period in self.time_periods_to_show:
            #todo: easy memoization... too lazy to do
            matching_data_points: List[TimeSeriesDataPoint] = []
            if time_period == TimePeriodsEnum.LATEST:
                time_segment_start = self.series[-1].date
                time_segment_end = self.series[-1].date
            elif time_period == TimePeriodsEnum.LAST_HOUR:
                time_segment_start = current_time - datetime.timedelta(hours=1)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_24HRS:
                time_segment_start = current_time - datetime.timedelta(hours=24)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_7_DAYS:
                time_segment_start = current_time - datetime.timedelta(days=7)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_30_DAYS:
                time_segment_start = current_time - datetime.timedelta(days=30)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_90_DAYS:
                time_segment_start = current_time - datetime.timedelta(days=90)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_365_DAYS:
                time_segment_start = current_time - datetime.timedelta(days=365)
                time_segment_end = current_time
            elif time_period == TimePeriodsEnum.LAST_365_DAYS:
                time_segment_start = current_time - datetime.timedelta(days=365)
                time_segment_end = current_time
            else:
                time_segment_start = self.series[0].date
                time_segment_end = current_time

            for tsdp in self.series:
                if time_segment_start <= tsdp.date <= time_segment_end:
                    # match
                    matching_data_points.append(tsdp)

            values.append(
                LabelledValueChip(
                    value=f"{self.aggregation_to_use(matching_data_points):,.2f}",
                    label=time_period.value
                )
            )

        info_card.add_content(
            LabelledChipGroup(values=values).render(hide_overflow=len(values) <= 4)
        )
        info_card.set_height(self.height)

        return info_card.render()

