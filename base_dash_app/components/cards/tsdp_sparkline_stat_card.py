import datetime
from math import floor, log, isnan
from typing import List, Dict

from dash import html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from base_dash_app.components.base_component import BaseComponent, ComponentWithInternalCallback
from base_dash_app.components.callback_utils.mappers import InputToState, InputMapping
from base_dash_app.components.cards.info_card import InfoCard
from base_dash_app.components.data_visualization.simple_line_graph import LineGraph
from base_dash_app.components.data_visualization.sparkline import Sparkline
from base_dash_app.components.labelled_value_chip import LabelledChipGroup, LabelledValueChip
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from base_dash_app.virtual_objects.timeseries.time_periods_enum import TimePeriodsEnum
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs

STAT_CARD_EXPAND_MODAL = "tsdp-stat-card-expand-modal"

STAT_CARD_EXPAND_BUTTON = "tsdp-stat-card-expand-button"


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
    #issue: (issue: 175): make generic stat card descriptor class
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
            description=None,
            show_expand_button=False,
            unit_is_suffix=False,
            lower_is_better=False,
    ):
        self.title = title
        self.unit = unit
        self.unit_is_suffix = unit_is_suffix
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.time_periods_to_show: List[TimePeriodsEnum] = time_periods_to_show or [TimePeriodsEnum.LAST_24HRS]
        self.aggregation_to_use: TsdpAggregationFuncs = aggregation_to_use
        self.use_human_formatting = use_human_formatting
        self.description = description
        self.show_expand_button = show_expand_button
        self.lower_is_better = lower_is_better


class TsdpSparklineStatCard(ComponentWithInternalCallback):

    @classmethod
    def handle_any_input(cls, *args, triggering_id, instance):
        if triggering_id.startswith(STAT_CARD_EXPAND_BUTTON):
            instance.modal_is_open = True

        return [instance.__render_tsdp_stat_card()]

    @staticmethod
    def get_input_to_states_map():
        return [
            InputToState(
                input_mapping=InputMapping(
                    input_id=STAT_CARD_EXPAND_BUTTON,
                    input_property="n_clicks",
                ),
                states=[]
            )
        ]

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
        smoothening=0.4,
        time_periods_to_show: List[TimePeriodsEnum] = None,
        aggregation_to_use: TsdpAggregationFuncs = TsdpAggregationFuncs.SUM,
        use_human_formatting=True,
        use_rg_color_scale=True,
        description=None,
        show_expand_button=False,
        unit_is_suffix=False,
        lower_is_better=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.series = sorted(series)
        self.title = title
        self.unit = unit
        self.unit_is_suffix = unit_is_suffix
        self.shape = shape
        self.smoothening = smoothening
        self.graph_height = graph_height
        self.time_periods_to_show: List[TimePeriodsEnum] = (
                sorted(time_periods_to_show, reverse=True) or [TimePeriodsEnum.LAST_24HRS]
        )
        self.aggregation_to_use: TsdpAggregationFuncs = aggregation_to_use
        self.use_human_formatting = use_human_formatting
        self.description = description
        self.modal_is_open = False
        self.show_expand_button = show_expand_button
        self.lower_is_better = lower_is_better

        self.values: Dict[TimePeriodsEnum, LabelledValueChip] = {
            time_period: None for time_period in self.time_periods_to_show
        }

        self.generate_data()

    def render(self, style_override=None, **kwargs):
        if style_override is None:
            style_override = {}

        return html.Div(
            children=[
                self.__render_tsdp_stat_card(**kwargs),
            ],
            style={**style_override},
            id={"type": TsdpSparklineStatCard.get_wrapper_div_id(), "index": self._instance_id},
        )

    def generate_data(self):
        current_time = datetime.datetime.now()
        for time_period in self.time_periods_to_show:
            if time_period not in self.values or self.values[time_period] is None:
                self.values[time_period] = (
                    LabelledValueChip(
                        value=" -",
                        label=time_period.get_label(),
                        lower_is_better=self.lower_is_better
                    )
                )

            # todo: easy memoization... too lazy to do
            if len(self.series) > 0:
                matching_data_points: List[TimeSeriesDataPoint] = []

                time_segment_start, time_segment_end = time_period.get_start_end_dates(current_time, self.series)
                # if is latest - use different delta:
                if time_period == TimePeriodsEnum.LATEST:
                    previous_time_segment_start = self.series[-2].date if len(self.series) > 1 else self.series[0].date
                else:
                    previous_time_segment_start = time_segment_start - time_period.value.delta

                previous_time_segment_end = current_time
                previous_matching_data_points: List[TimeSeriesDataPoint] = []

                for tsdp in self.series:
                    if time_segment_start <= tsdp.date <= time_segment_end:
                        # match
                        matching_data_points.append(tsdp)

                    if previous_time_segment_start <= tsdp.date <= previous_time_segment_end:
                        previous_matching_data_points.append(tsdp)

                numeric_value = value = self.aggregation_to_use(matching_data_points)
                previous_value = self.aggregation_to_use(previous_matching_data_points)

                if value is None:
                    value = 0  # todo: default value!

                if previous_value is None:
                    previous_value = 0

                is_negative = value < 0

                if self.use_human_formatting:
                    value = human_format(abs(value))
                else:
                    value = f"{abs(value):,.2f}"
            else:
                value = "-"
                numeric_value = None
                is_negative = False
                previous_value = None

            value = (
                f"{'-' if is_negative else ''}"
                f"{self.unit if self.unit is not None and not self.unit_is_suffix else ''}"
                f"{' ' if is_negative or self.unit is not None else ''}"
                f"{value}"
                f"{self.unit if self.unit is not None and self.unit_is_suffix else ''}"
            )

            self.values[time_period].value = value
            self.values[time_period].set_previous_value(numeric_value, previous_value)

    def __render_tsdp_stat_card(self, card_width=550, **kwargs):
        info_card = InfoCard()
        info_card.width = card_width

        sparkline = Sparkline(
            title=self.title, series=self.series,
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
                smoothening=self.smoothening,
                mouse_interactions=True
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

        chips_list = list(self.values.values())
        info_card.add_content(
            LabelledChipGroup(
                values=chips_list
            ).render(
                hide_overflow=len(chips_list) <= 4,
                show_percentages=True
            )
            # todo: make number of chips to show configurable
        )

        if self.show_expand_button:
            info_card.add_content(
                dbc.Button(
                    html.I(
                        className="fa-solid fa-expand",
                        style={"fontSize": "32px", "color": "black", "lineHeight": "32px"}
                    ),
                    color="light",
                    style={
                        "position": "absolute",
                        "right": "10px",
                        "padding": "10px",
                        "borderRadius": "10px",
                        "zIndex": "1000",
                        "top": "10px",
                        "height": "52px",
                        "display": "none" if len(self.series) == 0 else "inherit"
                    },
                    className="display_on_parent_hover_only",
                    id={"type": STAT_CARD_EXPAND_BUTTON, "index": self._instance_id},

                )
            )

            show_modal = self.modal_is_open
            self.modal_is_open = False
            info_card.add_content(
                dbc.Modal(
                    [
                        dbc.ModalBody(
                            children=[
                                sparkline.render(
                                    width=1100,
                                    height=600,
                                    shape=self.shape,
                                    smoothening=self.smoothening,
                                    show_x_axis=True,
                                    show_y_axis=True,
                                    mouse_interactions=True,
                                    show_custom_x_axis=False,
                                    fixed_range=False
                                )
                            ]
                        ),
                    ],
                    id={"type": STAT_CARD_EXPAND_MODAL, "index": self._instance_id},
                    size="xl",
                    is_open=show_modal,
                )
            )

        return info_card.render()

