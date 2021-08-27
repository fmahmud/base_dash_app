import datetime
from enum import Enum


class TaskRepeatPeriodEnum(Enum):
    DOES_NOT_REPEAT = ("Does not Repeat", 0)
    DAILY = ("Daily", 1)
    WEEKDAYS = ("Every Weekday", 2)
    HALF_WEEKLY = ("Half Weekly", 3)
    WEEKLY = ("Weekly", 4)
    FORTNIGHTLY = ("Fortnightly", 5)
    ANNUALLY = ("Annually", 6)

    def __init__(self, summary: str, order: int):
        self.summary = summary
        self.order = order

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __lt__(self, other):
        if type(other) != type(self):
            return True
        return self.order < other.order

    def __gt__(self, other):
        if type(other) != type(self):
            return False
        return self.order > other.order

    @staticmethod
    def get_next_occurrence(period: 'TaskRepeatPeriodEnum', previous_occurrence: datetime.datetime):
        if period == TaskRepeatPeriodEnum.DOES_NOT_REPEAT:
            raise Exception("Trying to repeat an unrepeatable task")
        elif period == TaskRepeatPeriodEnum.DAILY:
            return previous_occurrence + datetime.timedelta(days=1)
        elif period == TaskRepeatPeriodEnum.WEEKDAYS:
            if previous_occurrence.weekday() in [5, 6]:
                raise Exception("Provided weekend as first occurrence when repeating every weekday.")
            if previous_occurrence.weekday() == 4:
                return previous_occurrence + datetime.timedelta(days=3)
            return previous_occurrence + datetime.timedelta(days=1)
        elif period == TaskRepeatPeriodEnum.WEEKLY:
            return previous_occurrence + datetime.timedelta(weeks=1)
        elif period == TaskRepeatPeriodEnum.HALF_WEEKLY:
            return previous_occurrence + datetime.timedelta(days=3.5)
        elif period == TaskRepeatPeriodEnum.FORTNIGHTLY:
            return previous_occurrence + datetime.timedelta(weeks=2)
        elif period == TaskRepeatPeriodEnum.ANNUALLY:
            return previous_occurrence.replace(year=previous_occurrence.year + 1)