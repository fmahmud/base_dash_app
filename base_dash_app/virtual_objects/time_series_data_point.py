import datetime
from typing import Callable

from base_dash_app.virtual_objects.interfaces.graphable import Graphable


class TimeSeriesDataPoint(Graphable):
    def __init__(self, date: datetime.datetime, value: float,
                 label_func: Callable[[datetime.datetime, float], str] = None):
        self.date: datetime.datetime = date
        self.value: float = value
        self.label_func = label_func

    def get_x(self):
        return self.date

    def get_y(self):
        return self.value

    def get_label(self):
        if self.label_func:
            return self.label_func(self.date, self.value)
        return self.value

    def __lt__(self, other):
        return self.date < other.date
