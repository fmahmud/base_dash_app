import datetime
from abc import ABC


class Event(ABC):
    def __init__(self, date: datetime.datetime):
        self.date: datetime.datetime = date

    def get_date(self):
        return self.date

    def get_string_date(self):
        return self.date.strftime("%d/%m/%Y")

    def __lt__(self, other: 'Event'):
        return self.date < other.date