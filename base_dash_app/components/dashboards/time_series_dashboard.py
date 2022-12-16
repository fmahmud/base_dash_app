import datetime
from typing import List

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.cards.tsdp_sparkline_stat_card import TsdpStatCardDescriptor, TsdpSparklineStatCard
from base_dash_app.components.datatable.time_series_datatable_wrapper import TimeSeriesDataTableWrapper
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.timeseries.time_series import TimeSeries
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs


class DateRangeAggregatorDescriptor:
    def __init__(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        interval: datetime.timedelta,
        aggregation_method: TsdpAggregationFuncs = TsdpAggregationFuncs.MEAN
    ):
        self.start_date: datetime.datetime = start_date
        self.end_date: datetime.datetime = end_date
        self.interval: datetime.timedelta = interval
        self.aggregation_method: TsdpAggregationFuncs = aggregation_method
        self.all_dates = date_utils.enumerate_datetimes_between(self.start_date, self.end_date, self.interval)


class TimeSeriesWrapper:
    def __init__(
        self, timeseries: TimeSeries,
        stat_card_descriptors: List[TsdpStatCardDescriptor] = None,
        show_in_datatable=True, column_format=None, column_datatype="numeric",
    ):
        self.timeseries: TimeSeries = timeseries
        self.stat_card_descriptors: List[TsdpStatCardDescriptor] = stat_card_descriptors or []
        self.show_in_datatable = show_in_datatable
        self.column_format = column_format
        self.column_datatype = column_datatype


class SimpleTimeSeriesDashboard(BaseComponent):
    def __init__(
            self,
            title: str,
            base_date_range: DateRangeAggregatorDescriptor
    ):
        self.title: str = title

        self.time_series_wrappers = {}

        self.tsdp_dtw = TimeSeriesDataTableWrapper(
            title=title,
            start_date=base_date_range.start_date,
            end_date=base_date_range.end_date,
            interval_size=base_date_range.interval,
            aggregation_method=base_date_range.aggregation_method,
            # reload_data_function=wrapper_generate_data(2, datetime.timedelta(hours=1)) # todo!
        )

        # todo: reload each time series individually?
        #   push reload function into time series wrapper?

    def add_timeseries(self, tsw: TimeSeriesWrapper):
        if tsw.timeseries.unique_id in self.time_series_wrappers:
            raise Exception("Cannot add duplicate time series!")

        self.time_series_wrappers[tsw.timeseries.unique_id] = tsw

        if tsw.show_in_datatable:
            self.tsdp_dtw.add_timeseries(tsw.timeseries, format=tsw.column_format, datatype=tsw.column_datatype)

    def render(self, *args, **kwargs):
        stat_cards = [
            TsdpSparklineStatCard.init_from_descriptor(
                descriptor=sc_desc, series=tsw.timeseries.tsdps
            ).render()
            for uid, tsw in self.time_series_wrappers.items() for sc_desc in tsw.stat_card_descriptors
        ]

        return html.Div(
            children=[
                html.H1(self.title),
                html.Div(
                    children=stat_cards,
                    style={
                        "position": "relative",
                        "float": "left",
                        "clear": "left",
                        "padding": "10px",
                        "width": "100%",
                        "minHeight": "350px",
                        "display": "none" if len(stat_cards) == 0 else ""
                    },
                ),
                self.tsdp_dtw.render()
            ]
        )