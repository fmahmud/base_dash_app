import datetime
import logging
from typing import Optional

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.progressable import Progressable
from base_dash_app.virtual_objects.interfaces.resultable_event import CachedResultableEvent
from base_dash_app.virtual_objects.interfaces.resultable_event_series import CachedResultableEventSeries
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.result import Result
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject

# todo another time - probably not needed
"""
create an abstraction layer above job definition, job instance, virtual job prog cont., and job parameters
which can be used when creating a card. think of way to add hard coded params \

"""


class VirtualProgressContainer:
    def __init__(self, ):
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.prerequisites_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.completion_criteria_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = 0
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.completed: bool = False
        self.extras = {}
        self.logs = []
        self.startable_event: Optional['StartableEvent'] = None


class StartableEvent(CachedResultableEvent, Progressable):
    def __init__(self):
        CachedResultableEvent.__init__(
            self, result=Result(0, StatusesEnum.PENDING),
            date=datetime.datetime.now()
        )

        self.startable_event_series: Optional['StartableEventSeries'] = None
        self.prog_container: VirtualProgressContainer = VirtualProgressContainer()

    def get_progress(self):
        return self.prog_container.progress


class StartableEventSeries(CachedResultableEventSeries, Startable, VirtualFrameworkObject):
    def __init__(self, *args, name: str, **kwargs):
        CachedResultableEventSeries.__init__(self)
        Startable.__init__(self)
        VirtualFrameworkObject.__init__(*args, **kwargs)

        self.name: str = name
        self.logger = logging.getLogger(self.name)
        self.current_event: Optional[StartableEvent] = None


    def start(self, *args, **kwargs):
        pass