import datetime
from typing import List, Callable

from dash.dash_table.Format import Format

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.components.datatable.datatable_wrapper import DataTableWrapper
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.timeseries.time_series import TimeSeries
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs

TIMESTAMP_KEY = "timestamp"

RELOAD_DASH_BTN_ID = "RELOAD_DASH_BTN_ID"

DOWNLOAD_DATA_BTN_ID = "DOWNLOAD_DATA_BTN_ID"

DATA_TABLE_WRAPPER_DOWNLOAD_ID = "data-table-wrapper-download-id"


class TimeSeriesDataTableWrapper(BaseComponent):
    def __init__(
        self, title,
        start_date: datetime.datetime, end_date: datetime.datetime,
        interval_size: datetime.timedelta,
        aggregation_method: TsdpAggregationFuncs,
        reload_data_function: Callable[[], List[TimeSeries]] = None
    ):
        self.start_date: datetime.datetime = start_date
        self.end_date: datetime.datetime = end_date
        self.interval_size: datetime.timedelta = interval_size
        self.time_column = {
            "name": "Interval",
            "id": TIMESTAMP_KEY,
            "type": "datetime"
        }

        self.timeseries = {}
        self.aggregation_method: TsdpAggregationFuncs = aggregation_method
        self.reload_data_function = None
        if reload_data_function is not None:
            def wrapped_reload_data_function():
                new_data: List[TimeSeries] = reload_data_function()
                for series in new_data:
                    self.overwrite_timeseries(timeseries=series)

                return self.generate_data_array()
        else:
            def wrapped_reload_data_function():
                return self.generate_data_array()

        self.reload_data_function = wrapped_reload_data_function

        self.datatable = DataTableWrapper(
            title=title,
            columns=[self.time_column],
            reload_data_function=self.reload_data_function,
        )

    def add_timeseries(self, timeseries: TimeSeries, datatype: str = "text", format: Format = None):
        """

        :param timeseries:
        :param datatype: one of ["numeric", "text", "datetime", "any"]
        :param format:
        :return:
        """
        if timeseries.unique_id in self.timeseries:
            raise Exception("Cannot add same time series twice.")

        self.timeseries[timeseries.unique_id] = timeseries
        self.datatable.columns.append({
            "name": timeseries.title,
            "id": timeseries.unique_id,
            "type": datatype,
            "format": format
        })

    def overwrite_timeseries(self, timeseries):
        self.timeseries[timeseries.unique_id] = timeseries

    def generate_data_array(self):
        number_of_rows = (self.end_date - self.start_date) // self.interval_size + 1

        data_dict = {
            i: {
                TIMESTAMP_KEY: (i * self.interval_size) + self.start_date  # todo: missing columns
            } for i in range(number_of_rows)
        }

        # no aggregation yet
        for series_id, series in self.timeseries.items():
            for tsdp in series.tsdps:
                i = (tsdp.date - self.start_date) // self.interval_size

                if series_id not in data_dict[i]:
                    data_dict[i][series_id] = []

                data_dict[i][series_id].append(tsdp)

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