import datetime
from math import floor, log, isnan
from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.labelled_value_chip import LabelledChipGroup, LabelledValueChip
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from base_dash_app.virtual_objects.timeseries.time_periods_enum import TimePeriodsEnum
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs


def human_format(number):
    if number is None:
        raise Exception("Number was none")

    if isnan(number):
        number = 0

    if -1 < number < 1:
        return f"{number:.2f}"

    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0

    magnitude = int(floor(log(abs(number), k))) if number != 0 else 0
    return f"{number / k**magnitude:.2f}{units[magnitude]}"


red_to_green_color_scale = {
    -100: "rgba(180, 60, 50, 1)",
    -50: "rgba(230, 124, 115, 1)",
    -20: "rgba(243, 190, 185, 1)",
    -10: "rgba(255, 230, 230, 1)",
    0: "rgba(0, 0, 0, 1)",
    10: "rgba(230, 255, 50, 1)",
    20: "rgba(190, 243, 115, 1)",
    50: "rgba(124, 230, 185, 1)",
    100: "rgba(60, 180, 230, 1)",
}


class TsdpStatCardDescriptor:
    # todo: make generic stat card descriptor
    def __init__(
            self,
            title=None,
            unit: str = None,
            graph_height: int = 40,
            shape="spline",
            smoothening=0.8,
            time_periods_to_show: List[TimePeriodsEnum] = None,
            aggregation_to_use: TsdpAggregationFuncs = TsdpAggregationFuncs.SUM,
            use_human_formatting=True,
            use_rg_color_scale=True,
            description=None
    ):
        self.title = title
        self.unit = unit
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.time_periods_to_show: List[TimePeriodsEnum] = time_periods_to_show or [TimePeriodsEnum.LAST_24HRS]
        self.aggregation_to_use: TsdpAggregationFuncs = aggregation_to_use
        self.use_human_formatting = use_human_formatting
        self.description = description


class TsdpSparklineStatCard(BaseComponent):
    @staticmethod
    def init_from_descriptor(descriptor: TsdpStatCardDescriptor, series: List[TimeSeriesDataPoint]):
        return TsdpSparklineStatCard(
            **{"series": series, **vars(descriptor)}
        )

    def __init__(
        self,
        series: List[TimeSeriesDataPoint],
        title=None,
        unit: str = None,
        graph_height: int = 40,
        shape="spline",
        smoothening=0.8,
        time_periods_to_show: List[TimePeriodsEnum] = None,
        aggregation_to_use: TsdpAggregationFuncs = TsdpAggregationFuncs.SUM,
        use_human_formatting=True,
        use_rg_color_scale=True,
        description=None

    ):
        self.series = sorted(series)
        self.title = title
        self.unit = unit
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.time_periods_to_show: List[TimePeriodsEnum] = time_periods_to_show or [TimePeriodsEnum.LAST_24HRS]
        self.aggregation_to_use: TsdpAggregationFuncs = aggregation_to_use
        self.use_human_formatting = use_human_formatting
        self.description = description

    def render(self, style_override=None,  **kwargs):
        if style_override is None:
            style_override = {}

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
                    "marginTop": "10px", "overflow": "hidden", "height": "30px", "marginBottom": "0"
                }
            ),
        )

        if self.description:
            info_card.add_content(
                html.Pre(
                    self.description,
                    style={
                        "position": "relative", "float": "left", "clear": "left", "width": "100%",
                        "overflow": "hidden", "marginBottom": "5px",
                        "whiteSpace": "break-spaces"
                    }
                ),
            )

        current_time = datetime.datetime.now()
        values = []
        for time_period in self.time_periods_to_show:
            #todo: easy memoization... too lazy to do
            if len(self.series) > 0:
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

                value = self.aggregation_to_use(matching_data_points)
                if value is None:
                    value = 0  #todo: default value!

                if self.use_human_formatting:
                    value = human_format(value)
                else:
                    value = f"{value:,.2f}"
            else:
                value = "-"

            values.append(
                LabelledValueChip(
                    value=value,
                    label=time_period.value
                )
            )

            if self.unit is not None:
                values[-1].value = self.unit + values[-1].value

        info_card.add_content(
            LabelledChipGroup(values=values).render(hide_overflow=len(values) <= 4)
        )

        return info_card.render(
            style_override=style_override
        )

