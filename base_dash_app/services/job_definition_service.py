import datetime
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Type, List, Dict, Any, Tuple, FrozenSet, TypeVar, Optional, Union

from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.base_service import BaseService
from base_dash_app.virtual_objects.interfaces.selectable import Selectable
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.result import Result

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]
JobDefinitionImpl = TypeVar("JobDefinitionImpl", bound="JobDefinition")


class JobAlreadyRunningException(Exception):
    def __init__(self, job_id: int):
        self.job_id = job_id

    def __str__(self):
        return f"Job with id {self.job_id} is already running."


class JobDefinitionService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(
            service_name="JobDefinitionService",
            object_type=JobDefinition,
            **kwargs
        )

        self.threadpool_executor = ThreadPoolExecutor(max_workers=1)

        self.non_selectables_to_container_map: (
            Dict[int, Optional[VirtualJobProgressContainer]]
        ) = {}

        self.job_to_selectables_to_container_map: (
            Dict[int, Dict[Selectable, Optional[VirtualJobProgressContainer]]]
        ) = {}

    def get_containers_by_job_id(self, job_id: int, by_selectables=False) -> (
        Union[
            Dict[Selectable, VirtualJobProgressContainer],
            Optional[VirtualJobProgressContainer]
        ]
    ):
        if job_id < 1 or job_id is None:
            raise Exception(f"Invalid job id provided: {job_id}")

        if by_selectables:
            if job_id not in self.job_to_selectables_to_container_map:
                self.__cache_container_by_job_def(self.get_by_id(job_id))

            to_return = self.job_to_selectables_to_container_map[job_id]
            return to_return
        else:
            if job_id not in self.non_selectables_to_container_map:
                self.__cache_container_by_job_def(self.get_by_id(job_id))

            return self.non_selectables_to_container_map[job_id]

    def __cache_container_by_job_def(self, job_def: JobDefinitionImpl):
        single_selectable_param_name = type(job_def).single_selectable_param_name()
        if single_selectable_param_name is not None:
            if job_def.id not in self.job_to_selectables_to_container_map:
                self.job_to_selectables_to_container_map[job_def.id] = {}

            job_def.sync_single_selectable_data(self.dbm.get_session())
            self.job_to_selectables_to_container_map[job_def.id] = {
                selectable: self.job_to_selectables_to_container_map[job_def.id].get(selectable, None)
                for selectable in job_def.selectables
            }
        else:
            if job_def.id not in self.non_selectables_to_container_map:
                self.non_selectables_to_container_map[job_def.id] = None

    def get_by_id(self, id: int) -> Optional[JobDefinitionImpl]:
        session: Session = self.dbm.get_session()
        job_def: JobDefinitionImpl = session.query(JobDefinition).filter_by(id=id).first()
        if job_def is None:
            return None
        job_def.set_vars_from_kwargs(**self.produce_kwargs())
        self.__cache_container_by_job_def(job_def)

        return job_def

    def get_by_class(self, clazz):
        session: Session = self.dbm.get_session()
        job_def: JobDefinitionImpl = session.query(clazz).filter_by(job_class=clazz.__name__).first()

        if job_def is None:
            return None
        job_def.set_vars_from_kwargs(**self.produce_kwargs())
        self.__cache_container_by_job_def(job_def)
        return job_def

    def run_job(
        self, *args, job_def: JobDefinitionImpl,
        parameter_values: Dict[str, Any] = None,
        selectable: Selectable = None,
        log_level: LogLevel = LogLevelsEnum.WARNING.value,
        **kwargs
    ):
        if parameter_values is None:
            parameter_values = {}

        job_class: Type[JobDefinitionImpl] = type(job_def)
        single_selectable_param_name = job_class.single_selectable_param_name()
        is_single_selectable = selectable is not None and single_selectable_param_name is not None
        self.__cache_container_by_job_def(job_def)

        if not issubclass(job_class, JobDefinition):
            raise Exception(f"Provided job definition was not of a valid type. Was of type {job_class}.")

        if job_class == JobDefinition:
            raise Exception("Trying to execute a JobDefinition instead of a child class.")

        self.logger.debug("Starting run job")
        if is_single_selectable:
            parameter_values[single_selectable_param_name] = selectable.get_value()
            if (
                job_def.id in self.job_to_selectables_to_container_map
                    and selectable in self.job_to_selectables_to_container_map[job_def.id]
                    and self.job_to_selectables_to_container_map[job_def.id][selectable] is not None
            ):
                raise JobAlreadyRunningException(job_id=job_def.id)
        else:
            if (
                job_def.id in self.non_selectables_to_container_map
                    and self.non_selectables_to_container_map[job_def.id] is not None
            ):
                raise JobAlreadyRunningException(job_id=job_def.id)

        session: Session = self.dbm.get_session()

        current_instance = JobInstance()
        current_instance.job_definition_id = job_def.id
        current_instance.start_time = datetime.datetime.now()
        current_instance.date = current_instance.start_time
        current_instance.completion_criteria_status_id = StatusesEnum.IN_PROGRESS.value.id
        current_instance.set_status(StatusesEnum.IN_PROGRESS)
        current_instance.parameters = json.dumps(parameter_values)
        self.save(current_instance)
        if current_instance in session:
            session.expunge(current_instance)

        # todo: I don't like this flow - improve this
        current_instance.tooltip_id = current_instance.get_unique_id()

        kwargs["job_instance"] = current_instance
        kwargs["job_def"] = job_def

        job_progress_container: VirtualJobProgressContainer = VirtualJobProgressContainer(
            job_instance_id=current_instance.id,
            job_definition_id=job_def.id
        )

        if is_single_selectable:
            self.job_to_selectables_to_container_map[job_def.id][selectable] = job_progress_container
            job_progress_container.selectable = selectable
        else:
            self.non_selectables_to_container_map[job_def.id] = job_progress_container

        job_progress_container.start_time = current_instance.start_time
        job_progress_container.log_level = log_level

        kwargs["prog_container"] = job_progress_container
        kwargs["parameter_values"] = parameter_values

        def handle_completion(future):
            job_instance = session.query(JobInstance).filter_by(id=current_instance.id).first()
            job_instance.progress = job_progress_container.progress
            job_instance.end_time = job_progress_container.end_time
            job_instance.execution_status_id = job_progress_container.execution_status.value.id
            job_instance.completion_criteria_status_id = job_progress_container.completion_criteria_status.value.id
            job_instance.prerequisites_status_id = job_progress_container.prerequisites_status.value.id
            job_instance.end_reason = job_progress_container.end_reason
            job_instance.resultable_value = job_progress_container.result
            job_instance.result = Result(
                job_progress_container.result, job_progress_container.completion_criteria_status
            )
            job_instance.extras = json.dumps(job_progress_container.extras)
            job_instance.logs = json.dumps(job_progress_container.logs)

            self.save(job_instance)
            job_def.rehydrate_events_from_db(session=session)
            if is_single_selectable:
                session.refresh(job_progress_container.selectable)
                self.job_to_selectables_to_container_map[job_def.id][job_progress_container.selectable] = None
            else:
                self.non_selectables_to_container_map[job_def.id] = None
        try:
            self.threadpool_executor.submit(
                self.__do_execution, *args, **kwargs
            ).add_done_callback(handle_completion)

            return job_progress_container
            # self.__do_execution(*args, **kwargs)
        except Exception as e:
            raise e

    def get_status(self, job_instance: JobInstance):
        prereq_status = StatusesEnum.get_by_id(job_instance.prerequisites_status_id)
        execution_status = StatusesEnum.get_by_id(job_instance.execution_status_id)
        completion_criteria_status = StatusesEnum.get_by_id(job_instance.completion_criteria_status_id)

        if prereq_status in passing_statuses:
            if execution_status in passing_statuses:
                return completion_criteria_status
            else:
                return execution_status
        else:
            return prereq_status

    def __do_execution(
            self, *args, job_def: JobDefinition,
            prog_container: VirtualJobProgressContainer,
            parameter_values: Dict,
            **kwargs
    ):
        session: Session = self.dbm.new_session()

        try:
            self.logger.debug(f"Using new session: {session.hash_key}")

            self.logger.debug("checking prerequisites...")

            prerequisites_status: StatusesEnum = job_def.check_prerequisites(
                *args, session=session, prog_container=prog_container,
                parameter_values=parameter_values,
                **kwargs
            )

            prog_container.prerequisites_status = prerequisites_status
            self.logger.debug(f"prerequisite status was {prerequisites_status}")

            if prerequisites_status in [StatusesEnum.WARNING, StatusesEnum.SUCCESS]:
                self.logger.debug(f"executing job...")
                execution_status: StatusesEnum = job_def.start(
                    *args, session=session, prog_container=prog_container,
                    parameter_values=parameter_values,
                    **kwargs
                )

                prog_container.execution_status = execution_status
                self.logger.debug(f"execution status was {execution_status}")

                self.logger.debug(f"checking completion criteria...")

                completion_criteria_status = job_def.check_completion_criteria(
                    *args, session=session, prog_container=prog_container,
                    parameter_values=parameter_values,
                    **kwargs
                )

                prog_container.completion_criteria_status = completion_criteria_status

                self.logger.debug(f"completion status was {completion_criteria_status}")
        except Exception as e:
            stacktrace = traceback.format_exc()
            prog_container.end_reason = str(e)
            prog_container.completion_criteria_status = StatusesEnum.FAILURE
            self.logger.error(f"Exception occurred: {stacktrace}")
        finally:
            prog_container.end_time = datetime.datetime.now()
            self.logger.debug(f"end time = {prog_container.end_time}")

            self.logger.debug(f"status = {prog_container.get_status()}")

            prog_container.completed = True
            session.close()
            return prog_container
