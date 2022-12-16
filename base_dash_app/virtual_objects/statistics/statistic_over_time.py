import datetime
from typing import Dict, Optional, List, TYPE_CHECKING

from base_dash_app.virtual_objects.statistics.statistic import Statistic
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint

if TYPE_CHECKING:
    from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent


class StatisticOverTime:
    def __init__(self, statistic: Statistic, *, data: Dict[datetime.datetime, float] = None):
        self.statistic: Statistic = statistic
        self.data: Dict[datetime.datetime, float] = data if data is not None else {}

    def process_result(self, result: float, date: datetime.datetime):
        if result is None or date is None:
            return

        self.statistic.process_result(result)
        if date not in self.data:
            self.data[date] = 0.0

        self.data[date] = self.statistic.get_statistic()

    def process_resultable_event(self, result: "ResultableEvent"):
        """todo: get perspective in here? or delete this?"""
        self.process_result(result.get_result().result, result.get_date())

    def get_graphables(self, ordered=True):
        to_return = []
        for k, v in self.data.items():
            to_return.append(TimeSeriesDataPoint(k, v))

        if ordered:
            return sorted(to_return, key=lambda g: g.date)

        return to_return

    def get_first(self) -> Optional[TimeSeriesDataPoint]:
        if len(self.data.keys()) == 0:
            return None

        k = min(list(self.data.keys()))
        v = self.data[k]
        return TimeSeriesDataPoint(k, v)

    def get_last(self) -> Optional[TimeSeriesDataPoint]:
        if len(self.data.keys()) == 0:
            return None

        k = max(list(self.data.keys()))
        v = self.data[k]
        return TimeSeriesDataPoint(k, v)

    def get_last_n(self, n: int) -> List[TimeSeriesDataPoint]:
        sorted_keys = sorted(list(self.data.keys()))

        return [TimeSeriesDataPoint(k, self.data[k]) for k in sorted_keys[-n:]]

    def get_first_n(self, n: int) -> List[TimeSeriesDataPoint]:
        sorted_keys = sorted(list(self.data.keys()))

        return [TimeSeriesDataPoint(k, self.data[k]) for k in sorted_keys[:n]]