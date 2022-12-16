from enum import Enum


class TimePeriodsEnum(Enum):
    LATEST = "Latest"
    LAST_HOUR = "Last Hour"
    LAST_24HRS = "Last 24 Hours"
    LAST_7_DAYS = "Last 7 Days"
    LAST_30_DAYS = "Last 30 Days"
    LAST_90_DAYS = "Last 90 Days"
    LAST_365_DAYS = "Last 365 Days"

    ALL_TIME = "All Time"
