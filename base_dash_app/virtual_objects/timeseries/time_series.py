from typing import List

from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


class TimeSeries:
    def __init__(self, title, unique_id, unit=None):
        self.title: str = title
        self.unit: str = unit
        self.tsdps: List[TimeSeriesDataPoint] = []
        self.unique_id = unique_id

    def set_title(self, title: str):
        self.title = title
        return self

    def add_tsdp(self, tsdp: TimeSeriesDataPoint):
        self.tsdps.append(tsdp)
        return self

    def set_tsdps(self, tsdps: List[TimeSeriesDataPoint]):
        self.tsdps = [*tsdps]
        return self

    def sort_tsdps(self):
        self.tsdps = sorted(self.tsdps)

    def get_first_date(self):
        if len(self.tsdps) == 0:
            return None

        self.sort_tsdps()
        return self.tsdps[0].date

    def get_last_date(self):
        if len(self.tsdps) == 0:
            return None

        self.sort_tsdps()
        return self.tsdps[-1].date

