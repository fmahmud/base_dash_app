import datetime
from typing import Union

from dateutil.relativedelta import relativedelta

from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.timeseries.tsdp_aggregation_funcs import TsdpAggregationFuncs


class DateRangeAggregatorDescriptor:
    def __init__(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        interval: Union[datetime.timedelta, relativedelta],
        aggregation_method: TsdpAggregationFuncs = TsdpAggregationFuncs.MEAN
    ):
        self.start_date: datetime.datetime = start_date
        self.end_date: datetime.datetime = end_date
        self.interval: Union[datetime.timedelta, relativedelta] = interval
        self.aggregation_method: TsdpAggregationFuncs = aggregation_method
        self.all_dates = date_utils.enumerate_datetimes_between(self.start_date, self.end_date, self.interval)
