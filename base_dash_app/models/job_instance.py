import datetime

from sqlalchemy import Column, Integer, Sequence, Float, orm, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.virtual_objects.interfaces.progressable import Progressable
from base_dash_app.virtual_objects.interfaces.resultable_event import CachedResultableEvent
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.interfaces.stoppable import Stoppable
from base_dash_app.virtual_objects.result import Result

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]


class JobInstance(CachedResultableEvent, Progressable, BaseModel):
    __tablename__ = "job_instances"

    id = Column(Integer, Sequence("job_instances_id_seq"), primary_key=True)
    job_definition_id = Column(Integer, ForeignKey("job_definitions.id"))

    job_definition = relationship("JobDefinition", back_populates="job_instances")

    resultable_value = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    parameters = Column(String)  # json representation of provided params

    progress = Column(Float, default=0.0)
    execution_status_id = Column(Integer, default=5)
    prerequisites_status_id = Column(Integer, default=5)
    completion_criteria_status_id = Column(Integer, default=5)
    end_reason = Column(String)
    extras = Column(String)
    logs = Column(String)

    def __repr__(self):
        return vars(self)

    def __str__(self):
        pass

    def get_formatted_start_time(self, format="%Y-%m-%d %H:%M"):
        if self.start_time is not None:
            return self.start_time.strftime(format)
        return "Unknown"

    def get_formatted_end_time(self, format="%Y-%m-%d %H:%M"):
        if self.end_time is not None:
            return self.end_time.strftime(format)
        return "Unknown"

    def get_progress(self):
        return self.progress

    def __init__(self, *args, **kwargs):
        Startable.__init__(self)
        Stoppable.__init__(self)
        CachedResultableEvent.__init__(
            self, result=Result(0, StatusesEnum.PENDING),
            date=datetime.datetime.now()
        )

        # self.status: StatusesEnum = StatusesEnum.PENDING
        self.job_definition_id = None
        self.id = None

    @orm.reconstructor
    def init_on_load(self):
        Startable.__init__(self)
        Stoppable.__init__(self)
        CachedResultableEvent.__init__(
            self, result=Result(
                self.resultable_value,
                StatusesEnum.get_by_id(self.completion_criteria_status_id)
            ),
            date=self.start_time,
            tooltip_id=self.get_unique_id()
        )

    def get_unique_id(self):
        return f"job-def-{self.job_definition_id}-instance-id-{self.id}"

    def __hash__(self):
        return hash(self.get_unique_id())

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.id == other.id and self.job_definition is other.job_definition

    def get_name(self):
        if self.job_definition is None:
            return "Undefined Instance"
        if self.end_reason is None or self.end_reason == "":
            return f"{self.get_string_date()} - {self.result.status.value.name}"
        return f"{self.get_string_date()} - {self.end_reason}"

    def get_header(self) -> (str, dict):
        return self.get_name(), {}

    def get_text(self) -> (str, dict):
        pass

    def get_extras(self):
        pass

    def get_link(self) -> str:
        pass
