import logging
from typing import Optional, List, Dict

from sqlalchemy import Column, Integer, Sequence, String, orm, Boolean
from sqlalchemy.orm import relationship

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.virtual_objects.interfaces.resultable_event_series import ResultableEventSeries, \
    CachedResultableEventSeries
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.interfaces.stoppable import Stoppable
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject


class JobDefinition(CachedResultableEventSeries, Startable, Stoppable, BaseModel, VirtualFrameworkObject):
    __tablename__ = "job_definitions"

    id = Column(Integer, Sequence("job_definitions_id_seq"), primary_key=True)
    name = Column(String)
    job_class = Column(String)
    job_instances = relationship("JobInstance", back_populates="job_definition")
    parameters = relationship("JobDefinitionParameter", back_populates="job_definition")

    repeats = Column(Boolean, default=False)
    seconds_between_runs = Column(Integer, default=0)
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

    @classmethod
    def force_update(cls):
        return False

    @classmethod
    def construct_instance(cls, **kwargs):
        if cls == JobDefinition:
            raise Exception("Cannot make instance of class JobDefinition.")

        raise Exception(f"Class {cls} needs to override construct_instance function.")

    @classmethod
    def autoinitialize(cls):
        """
        If True, at runtime, the system checks if there is an instance of this class in the DB.
            If there is no instance in the DB, application will use construct_instance method
            to create default instance and save to DB. If method is not defined, or not overridden,
            an exception will be raised and the application will fail to start.
        """
        return False

    @classmethod
    def get_general_params(cls):
        return []

    def __init__(self, *args, **kwargs):
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)
        VirtualFrameworkObject.__init__(self, **kwargs)

        self.__current_job_instance: Optional[JobInstance] = None
        self.current_prog_container: Optional[VirtualJobProgressContainer] = None
        self.logger = logging.getLogger(self.name)

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

    def get_parameters(self) -> List[JobDefinitionParameter]:
        return self.parameters

    def get_params_dict(self) -> Dict[str, JobDefinitionParameter]:
        if len(self.parameters) > 0:
            return {jpd.variable_name: jpd for jpd in self.parameters}
        return {}

    def check_completion_criteria(
            self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
            **kwargs
    ) -> StatusesEnum:
        """
        Default completion criteria relies on prerequisites and execution statuses

        :param parameter_values:
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

    def check_prerequisites(
        self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
        **kwargs
    ) -> StatusesEnum:
        pass

    def start(
        self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
        **kwargs
    ) -> StatusesEnum:
        pass

    def stop(
        self, *args, prog_container: VirtualJobProgressContainer, parameter_values: Dict,
        **kwargs
    ) -> StatusesEnum:
        pass
