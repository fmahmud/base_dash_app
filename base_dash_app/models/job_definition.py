import logging
from typing import Optional, List, Dict

from sqlalchemy import Column, Integer, Sequence, String, orm, Boolean
from sqlalchemy.orm import relationship

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.virtual_objects.interfaces.resultable_event_series import ResultableEventSeries, \
    CachedResultableEventSeries
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.interfaces.stoppable import Stoppable
from base_dash_app.virtual_objects.job_parameter import JobParameterDefinition
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer


class JobDefinition(CachedResultableEventSeries, Startable, Stoppable, BaseModel):
    __tablename__ = "job_definitions"

    id = Column(Integer, Sequence("job_definitions_id_seq"), primary_key=True)
    name = Column(String)
    job_class = Column(String)
    job_instances = relationship("JobInstance", back_populates="job_definition")
    repeats = Column(Boolean)
    seconds_between_runs = Column(Integer)
    description = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "job_definitions",
        "polymorphic_on": job_class,
    }

    def __lt__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __repr__(self):
        pass

    def __str__(self):
        pass

    def set_base_service_args(self, *args, service_provider, api_provider, **kwargs):
        self.service_provider = service_provider
        self.api_provider = api_provider

    def __init__(self, *args, service_provider, api_provider, description: str = None, **kwargs):
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)

        self.description = description
        self.__current_job_instance: Optional[JobInstance] = None
        self.current_prog_container: Optional[VirtualJobProgressContainer] = None
        self.logger = logging.getLogger(self.name)
        self.service_provider = service_provider
        self.api_provider = api_provider

    @orm.reconstructor
    def init_on_load(self):
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)

        self.__current_job_instance: Optional[JobInstance] = None
        self.current_prog_container: Optional[VirtualJobProgressContainer] = None
        self.logger = logging.getLogger(self.name)

        self.rehydrate_events_from_db()

    def rehydrate_events_from_db(self):
        for ji in self.job_instances:
            ji: JobInstance
            self.process_result(ji.get_result(), ji)

    def is_in_progress(self):
        return self.current_prog_container is not None

    def get_progress(self):
        if self.is_in_progress():
            return self.current_prog_container.progress

    @classmethod
    def get_parameters(cls) -> List[JobParameterDefinition]:
        return []

    @classmethod
    def get_params_dict(cls) -> Dict[str, JobParameterDefinition]:
        return {jpd.param_name: jpd for jpd in cls.get_parameters()}

    def check_completion_criteria(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        """
        Default completion criteria relies on prerequisites and execution statuses

        :param args:
        :param prog_container:
        :param kwargs:
        :return:
        """
        if prog_container.prerequisites_status != StatusesEnum.SUCCESS:
            return prog_container.prerequisites_status

        if prog_container.execution_status != StatusesEnum.SUCCESS:
            return prog_container.execution_status

        return StatusesEnum.SUCCESS

    def check_prerequisites(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        pass

    def start(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        pass

    def stop(self, *args, prog_container: VirtualJobProgressContainer, **kwargs) -> StatusesEnum:
        pass

    # def run_job(self, *args, **kwargs):
    #     global threadpool_executor
    #
    #     if self.__current_thread is not None or self.__current_job_instance is not None:
    #         raise Exception("Can't run two instances of the same job at the same time")
    #
    #     self.__current_job_instance = JobInstance(self, len(self.events) + 1)
    #     try:
    #         self.__current_thread = threadpool_executor.submit(
    #             self.__current_job_instance.start, *args, **kwargs
    #         )
    #     except Exception as e:
    #         raise e
