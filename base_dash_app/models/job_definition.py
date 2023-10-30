import abc
import datetime
import json
import logging
import time
from abc import ABC
from operator import or_
from timeit import timeit
from typing import Optional, List, Dict, Any, Tuple, FrozenSet, TypeVar, Type

from sqlalchemy import Column, Integer, Sequence, String, orm, Boolean, select, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Session

from base_dash_app.enums.log_levels import LogLevelsEnum
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.base_model import BaseModel
from base_dash_app.models.job_definition_parameter import JobDefinitionParameter
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.virtual_objects.interfaces.resultable_event_series import ResultableEventSeries, \
    CachedResultableEventSeries
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.interfaces.stoppable import Stoppable
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.virtual_framework_obj import VirtualFrameworkObject


class JobDefinition(CachedResultableEventSeries, Startable, Stoppable, BaseModel, VirtualFrameworkObject):
    def get_label(self):
        return self.name

    def get_value(self):
        return self.id

    def get_start_time(self):
        pass

    def get_end_time(self):
        pass

    __tablename__ = "job_definitions"

    id = Column(Integer, Sequence("job_definitions_id_seq"), primary_key=True)
    name = Column(String)
    job_class = Column(String)
    job_instances = relationship(
        "JobInstance",
        back_populates="job_definition",
        order_by="desc(JobInstance.start_time)",
        lazy="select"
    )

    parameters = relationship("JobDefinitionParameter", back_populates="job_definition")

    repeats = Column(Boolean, default=False)
    seconds_between_runs = Column(Integer, default=0)
    description = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "job_definitions",
        "polymorphic_on": job_class,
    }

    def __lt__(self, other):
        # todo
        pass

    def __eq__(self, other):
        # todo
        pass

    def __hash__(self):
        # todo
        pass

    def __repr__(self):
        return vars(self)

    def __str__(self):
        # todo
        pass

    @classmethod
    def get_selectable_by_value(cls, value: Any, session: Session) -> Optional[Selectable]:
        selectable_type = cls.get_selectable_type()
        param_name = cls.single_selectable_param_name()

        if selectable_type is None:
            return None

        if issubclass(selectable_type, BaseModel):
            return session.query(selectable_type).get(value)
        else:
            cached_selectables = cls.get_selectables_by_param_name(param_name, session)
            for cached_selectable in cached_selectables:
                if cached_selectable.get_value() == value:
                    return cached_selectable

        return None

    @classmethod
    def get_selectable_type(cls) -> Optional[Type[Selectable]]:
        return None

    @classmethod
    def get_selectable_for_instance(cls, instance: "JobInstance", session: Session) -> Optional[Selectable]:
        instance_params = instance.parameters
        if instance_params is None or instance_params == "" or instance_params == "{}":
            return None

        param_dict = json.loads(instance_params)
        param_name = cls.single_selectable_param_name()
        if param_name not in param_dict:
            return None

        param_value = param_dict[param_name]
        selectable = cls.get_selectable_by_value(param_value, session)

        return selectable

    def get_in_progress_instances_by_selectable(self, session: Session) -> List[JobInstance]:
        # note time
        current_time = time.time_ns()
        # check for new in progress instances
        param_substring_comma = "%, " + f"\"{type(self).single_selectable_param_name()}\": %"
        param_substring_brace = "{" + f"\"{type(self).single_selectable_param_name()}\": %"

        in_progress_instances = (
            session.query(JobInstance)
            .filter_by(end_time=None)
            .filter_by(job_definition_id=self.id)
            .filter(JobInstance.execution_status_id != StatusesEnum.FAILURE.value.id)
            .filter(
                or_(
                    JobInstance.parameters.like(param_substring_comma),
                    JobInstance.parameters.like(param_substring_brace)
                )
            )
            .all()
        )

        finish_time = time.time_ns()
        self.logger.info(f"get_in_progress_instances_by_selectable took {(finish_time - current_time) / 10**6} ms")
        return in_progress_instances

    @hybrid_property
    def latest_start_time(self):
        # This part works at the instance level.
        return max((instance.start_time for instance in self.job_instances), default=None)

    @latest_start_time.expression
    def latest_child_timestamp(cls):
        # This part works at the class/query level.
        return (
            select([func.max(JobInstance.start_time)])
            .where(JobInstance.job_definition_id == cls.id)
            .label('latest_start_time')
        )

    @classmethod
    def get_latest_exec_for_selectable(cls, selectable: Selectable, session: Session) -> Optional[JobInstance]:
        return None

    @classmethod
    @abc.abstractmethod
    def get_selectables_by_param_name(
        cls,
        param_name: str,
        session: Session
    ) -> List[Selectable]:
        """
        Child classes of JobDefinition must implement this function.
        :param session:
        :param param_name:
        :return:
        """
        pass

    @classmethod
    def force_update(cls):
        """
        NOT IN USE ATM.
        At runtime, if autoinitialize returns True for this child class, the existing instance
        in the DB will have its data overridden by the data present in this instance. If False,
        no action will be taken.
        :return:
        """
        return False

    @classmethod
    @abc.abstractmethod
    def construct_instance(cls, **kwargs):
        pass

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

    @classmethod
    @abc.abstractmethod
    def single_selectable_param_name(cls) -> Optional[str]:
        return None

    def __init__(
            self,
            dbm: DbManager = None,
            *args, **kwargs
    ):
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)
        VirtualFrameworkObject.__init__(self, **kwargs)

        self.cached_selectables: List[CachedSelectable] = []
        self.single_selectable_param_name: str = type(self).single_selectable_param_name()

        if dbm is not None:
            with dbm as dbm:
                session: Session = dbm.get_session()
                self.sync_single_selectable_data(session=session)

        self.logger = logging.getLogger(self.name)

    def sync_single_selectable_data(self, session: Session):
        if self.single_selectable_param_name is not None:
            self.cached_selectables = type(self).get_selectables_by_param_name(
                self.single_selectable_param_name,
                session=session
            )

    @orm.reconstructor
    def init_on_load(self):
        JobDefinition.__init__(self)
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)
        self.logger = logging.getLogger(self.name)
        self.rehydrate_events_from_db()

    def rehydrate_events_from_db(self):
        self.clear_all()

        for ji in self.job_instances:
            ji: JobInstance
            self.process_result(ji.get_result(), ji)

    def is_in_progress(self) -> bool:
        raise Exception("Deprecated")

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
