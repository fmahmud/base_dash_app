import datetime
from abc import ABC, abstractmethod
from typing import Callable, Optional

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.event import Event
from base_dash_app.virtual_objects.interfaces.linkable import Linkable
from base_dash_app.virtual_objects.interfaces.listable import Listable
from base_dash_app.virtual_objects.interfaces.nameable import Nameable
from base_dash_app.virtual_objects.interfaces.resultable import Resultable
from base_dash_app.virtual_objects.result import Result


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
    def get_tooltip_id(self):
        return self.tooltip_id

    def get_event_dot(self, style_override=None):
        if style_override is None:
            style_override = {}

        from base_dash_app.components.historicals.historical_dots import render_event_rectangle
        return render_event_rectangle(
            self.get_status_color(),
            dot_style_override={
                "borderRadius": "7px",
                "marginRight": "10px",
                "marginLeft": "10px",
                "animation": "blinker_animation 0.6s cubic-bezier(1, 0, 0, 1) infinite alternate"
                if self.result.status == StatusesEnum.IN_PROGRESS
                else "none",
                **style_override
            },
            tooltip_id=self.tooltip_id
        )

    def get_status_color(self, *, perspective=None) -> StatusesEnum:
        return self.result.status

    def __eq__(self, other):
        return self.original_re.__eq__(other)

    def get_link(self) -> str:
        return self.original_re.get_link()

    def get_name(self):
        return self.original_re.get_name()

    def get_header(self) -> (str, dict):
        text, style = self.original_re.get_header()
        style["color"] = self.result.status.value
        return text, style

    def get_text(self) -> (str, dict):
        return self.original_re.get_text()

    def get_extras(self):
        return self.original_re.get_extras()

    def __init__(
            self, result: Result, date: datetime.datetime,
            *, original_re: ResultableEvent = None, tooltip_id=None):
        super().__init__(date)
        self.result: Result = result
        self.original_re: ResultableEvent = original_re
        self.tooltip_id = tooltip_id

    def get_result(self, *, perspective: Callable[['Resultable'], Optional[int]] = None) -> Result:
        return self.result

    def __hash__(self):
        return self.original_re.__hash__()