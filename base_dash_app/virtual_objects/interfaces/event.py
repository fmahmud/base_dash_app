import datetime
from abc import ABC


class Event(ABC):
    def __init__(self, date: datetime.datetime):
        self.date: datetime.datetime = date

    def get_date(self):
        return self.date

    def get_string_date(self):
        return self.date.strftime("%Y-%m-%d %H:%M")

    def __lt__(self, other):
        if type(other) != type(self):
            return False
        if other.date is None or self.date is None:
            #todo: better comparison between None and nonNones
            return False

        return self.date < other.date
