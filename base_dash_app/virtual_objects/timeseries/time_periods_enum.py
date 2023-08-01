import datetime
from enum import Enum
from typing import List, Callable

from dateutil.relativedelta import relativedelta

from base_dash_app.virtual_objects.interfaces.event import Event


class TimePeriods:
    def __init__(self, name, delta: relativedelta, get_start_date_override: Callable = None):
        self.name = name
        self.delta = delta
        if get_start_date_override:
            self.get_start_date = get_start_date_override

    def get_start_end_dates(self, current_time, events: List[Event] = None):
        return current_time - self.delta, current_time

    def __lt__(self, other):
        if type(self) == type(other):
            return datetime.datetime.now() + self.delta < datetime.datetime.now() + other.delta

        return False

class TimePeriodsEnum(Enum):
    LATEST = TimePeriods(
        "Latest", relativedelta(minutes=1), lambda current_time, events: (events[-1].date, events[-1].date)
    )
    EARLIEST = TimePeriods(
        "Earliest", relativedelta(days=1), lambda current_time, events: (events[0].date, events[0].date)
    )

    LAST_HOUR = TimePeriods("Last Hour", relativedelta(hours=1))
    LAST_24HRS = TimePeriods("Last 24 Hours", relativedelta(days=1))
    LAST_7_DAYS = TimePeriods("Last 7 Days", relativedelta(days=7))
    LAST_30_DAYS = TimePeriods("Last 30 Days", relativedelta(days=30))
    LAST_MONTH = TimePeriods("Last Month", relativedelta(months=1))
    LAST_90_DAYS = TimePeriods("Last 90 Days", relativedelta(days=90))
    LAST_QUARTER = TimePeriods("Last Quarter", relativedelta(months=3))
    LAST_YEAR = TimePeriods("Last Year", relativedelta(years=1))

    ALL_TIME = TimePeriods("All Time", relativedelta(days=1), lambda current_time, events: (events[0].date, current_time))

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return type(self) == type(other) and hash(self) == hash(other)

    def __lt__(self, other):
        return self.value < other.value

    def get_label(self):
        return self.value.name

    def get_start_end_dates(self, current_time, events: List[Event] = None):
        return self.value.get_start_end_dates(current_time, events)
