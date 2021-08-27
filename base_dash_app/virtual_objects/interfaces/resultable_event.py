import datetime
from abc import ABC, abstractmethod
from typing import Callable, Optional

from base_dash_app.virtual_objects.interfaces.event import Event
from base_dash_app.virtual_objects.interfaces.linkable import Linkable
from base_dash_app.virtual_objects.interfaces.listable import Listable
from base_dash_app.virtual_objects.interfaces.nameable import Nameable
from base_dash_app.virtual_objects.interfaces.resultable import Resultable


class ResultableEvent(Resultable, Nameable, Listable, Linkable, Event, ABC):
    def __init__(self, date: datetime.datetime):
        Resultable.__init__(self)
        Event.__init__(self, date)

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass


class CachedResultableEvent(ResultableEvent):
    def __eq__(self, other):
        return self.original_re.__eq__(other)

    def get_link(self) -> str:
        return self.original_re.get_link()

    def get_name(self):
        return self.original_re.get_name()

    def get_header(self) -> (str, dict):
        text, style = self.original_re.get_header()
        style["color"] = Resultable.get_status_color_from_result(self.result).value
        return text, style

    def get_text(self) -> (str, dict):
        return self.original_re.get_text()

    def get_extras(self):
        return self.original_re.get_extras()

    def __init__(self, result: float, date: datetime.datetime, *, original_re: ResultableEvent = None):
        super().__init__(date)
        self.result = result
        self.original_re: ResultableEvent = original_re

    def get_result(self, *, perspective: Callable[['Resultable'], Optional[int]] = None):
        return self.result

    def __hash__(self):
        return self.original_re.__hash__()