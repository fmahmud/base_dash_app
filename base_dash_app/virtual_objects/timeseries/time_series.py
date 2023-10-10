import abc
from typing import List, Optional

from base_dash_app.components.data_visualization.simple_line_graph import GraphableSeries
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


class AbstractTimeSeries(GraphableSeries, abc.ABC):
    def __init__(self):
        super().__init__()

    def get_name(self):
        return self.get_title()

    @abc.abstractmethod
    def get_title(self):
        pass

    @abc.abstractmethod
    def get_unique_id(self):
        pass

    @abc.abstractmethod
    def get_description(self):
        pass

    def add_tsdp(self, tsdp: TimeSeriesDataPoint):
        self.data.append(tsdp)
        return self

    def set_tsdps(self, tsdps: List[TimeSeriesDataPoint]):
        self.data = [*tsdps]
        return self

    def get_tsdps(self):
        return self.data

    def sort_tsdps(self):
        self.data = sorted(self.data)

    def get_first_date(self):
        if len(self.data) == 0:
            return None

        self.sort_tsdps()
        return self.data[0].date

    def get_last_date(self):
        if len(self.data) == 0:
            return None

        self.sort_tsdps()
        return self.data[-1].date


class TimeSeries(AbstractTimeSeries):
    def get_title(self):
        return self.title

    def get_unique_id(self):
        return self.unique_id

    def get_description(self):
        return self.description

    def __init__(self, title, unique_id, unit=None, description=None, lower_is_better=False):
        super().__init__()
        self.title: str = title
        self.unique_id: str = unique_id
        self.unit: Optional[str] = unit
        self.description: Optional[str] = description
        self.lower_is_better: bool = lower_is_better


