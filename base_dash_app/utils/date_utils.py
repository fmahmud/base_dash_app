import datetime
from typing import Union

from dateutil.relativedelta import relativedelta
import math

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 24
SECONDS_IN_WEEK = SECONDS_IN_DAY * 7

def get_num_days_in_month(month_number, year=datetime.datetime.now().year):
    from calendar import monthrange
    return monthrange(year, month_number)[1]


def readable_time_since(moment: datetime.datetime):
    if moment is None:
        return "Never"

    difference = (datetime.datetime.now() - moment).total_seconds()

    if difference < SECONDS_IN_MINUTE:
        # use seconds
        unit = "second"
    elif difference < SECONDS_IN_HOUR:
        # use minutes
        difference = difference / SECONDS_IN_MINUTE
        unit = "minute"
    elif difference < SECONDS_IN_DAY:
        # use hours
        difference = difference / SECONDS_IN_HOUR
        unit = "hour"
    elif difference < SECONDS_IN_WEEK:
        # use days
        difference = difference / SECONDS_IN_DAY
        unit = "day"
    else:
        difference = difference / SECONDS_IN_WEEK
        unit = "week"

    return f"{round(difference, 0):.0f} {unit}{'s' if round(difference) != 1 else ''}"


def enumerate_datetimes_between(
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    interval: Union[datetime.timedelta, relativedelta]
):
    if end_date < start_date:
        raise Exception("End date cannot be before start date")
    moments = []
    current = start_date
    while current < end_date:
        moments.append(current)
        current = current + interval

    return moments
