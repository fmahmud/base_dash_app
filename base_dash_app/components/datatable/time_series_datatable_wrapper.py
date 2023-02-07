import datetime
from typing import List, Callable, Union, Dict, Any

from dash.dash_table.Format import Format

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.timeseries.time_series import AbstractTimeSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs
from dateutil.relativedelta import relativedelta

TIMESTAMP_KEY = "timestamp"


class TimeSeriesDataTableWrapper(BaseComponent):
    def __init__(
        self, title,
        start_date: datetime.datetime, end_date: datetime.datetime,
        interval_size: Union[datetime.timedelta, relativedelta],
        aggregation_method: TsdpAggregationFuncs,
        reload_data_function: Callable[[], List[AbstractTimeSeries]] = None,
        hide_toolbar=False,
    ):
        self.start_date: datetime.datetime = start_date
        self.end_date: datetime.datetime = end_date
        self.interval_size: datetime.timedelta = interval_size
        self.time_column = {
            "name": "Interval",
            "id": TIMESTAMP_KEY,
            "type": "datetime"
        }

        self.timeseries: Dict[str, AbstractTimeSeries] = {}
        self.aggregation_method: TsdpAggregationFuncs = aggregation_method
        self.hide_toolbar = hide_toolbar
        self.reload_data_function = None
        if reload_data_function is not None:
            def wrapped_reload_data_function():
                new_data: List[AbstractTimeSeries] = reload_data_function()
                for series in new_data:
                    self.overwrite_timeseries_data(timeseries=series, data=series.get_tsdps())

                return self.generate_data_array()
        else:
            def wrapped_reload_data_function():
                return self.generate_data_array()

        self.reload_data_function = wrapped_reload_data_function

        self.datatable = DataTableWrapper(
            title=title,
            columns=[self.time_column],
            reload_data_function=self.reload_data_function,
            hide_toolbar=self.hide_toolbar
        )

    def add_timeseries(self, timeseries: AbstractTimeSeries, datatype: str = "text", format: Format = None):
        """

        :param timeseries:
        :param datatype: one of ["numeric", "text", "datetime", "any"]
        :param format:
        :return:
        """
        if timeseries.get_unique_id() in self.timeseries:
            raise Exception("Cannot add same time series twice.")

        self.timeseries[timeseries.get_unique_id()] = timeseries
        self.datatable.columns.append({
            "name": timeseries.get_title(),
            "id": timeseries.get_unique_id(),
            "type": datatype,
            "format": format
        })

    def overwrite_timeseries_data(self, timeseries: AbstractTimeSeries, data: List[TimeSeriesDataPoint]):
        if timeseries.get_unique_id() not in self.timeseries:
            raise Exception(f"Couldn't find timeseries with id: {timeseries.get_unique_id()}")

        self.timeseries[timeseries.get_unique_id()].set_tsdps(data)

    def generate_data_array(self):
        interval_start = self.start_date
        interval_end = min(self.start_date + self.interval_size, self.end_date)
        data_dict: Dict[tuple, Any] = {}
        while interval_start <= self.end_date:
            data_dict[tuple([interval_start, min(interval_end, self.end_date)])] = {
                TIMESTAMP_KEY: interval_start  # todo: missing columns
            }

            interval_start += self.interval_size
            interval_end += self.interval_size

        # no aggregation yet
        for series_id, series in self.timeseries.items():
            series.sort_tsdps()
            interval_start = self.start_date
            interval_end = min(self.start_date + self.interval_size, self.end_date)
            for tsdp in series.tsdps:
                tsdp: TimeSeriesDataPoint
                while tsdp.date >= interval_end:
                    interval_start += self.interval_size
                    interval_end += self.interval_size

                key_tuple = tuple([interval_start, min(interval_end, self.end_date)])
                if series_id not in data_dict[key_tuple]:
                    data_dict[key_tuple][series_id] = []

                data_dict[key_tuple][series_id].append(tsdp)

        # do aggregation
        for i, data in data_dict.items():
            for k, v in data.items():
                if k == TIMESTAMP_KEY:
                    continue

                data[k] = self.aggregation_method(v)

        # flatten to list:
        return list(data_dict.values())

    def render(self, *args, **kwargs):
        return self.datatable.render()