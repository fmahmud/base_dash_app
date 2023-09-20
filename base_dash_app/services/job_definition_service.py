import datetime
import gc
import json
import logging
import os
import pprint
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from operator import or_
from typing import Type, List, Dict, Any, Tuple, FrozenSet, TypeVar, Optional, Union

from celery import shared_task
from celery.signals import task_prerun, task_postrun
from flask import has_app_context
from redis import Redis, StrictRedis
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session
from sqlalchemy.orm.scoping import ScopedSession

from base_dash_app.application.celery_decleration import CelerySingleton
from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.db_utils import DbManager
from base_dash_app.virtual_objects.interfaces.selectable import Selectable, CachedSelectable
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer, ContainerNotFoundError
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

        with (self.dbm as dbm):
            session: Session = dbm.get_session()
            job_def: JobDefinitionImpl = session.query(JobDefinition).filter_by(id=job_id).first()

            if by_selectables:
                job_class: Type[JobDefinitionImpl] = type(job_def)

                if job_id not in self.job_to_selectables_to_container_map:
                    self.__cache_container_by_job_def(self.get_by_id(job_id, session=session))

                in_progress_instances = job_def.get_in_progress_instances_by_selectable(
                    session=session
                )
                # log the in progress instances
                self.logger.debug(f"Num in progress instances = {len(in_progress_instances)}")

                for in_progress_instance in in_progress_instances:
                    selectable: Selectable = job_class.get_selectable_for_instance(
                        instance=in_progress_instance, session=session
                    )

                    if selectable not in self.job_to_selectables_to_container_map[job_id]:
                        self.job_to_selectables_to_container_map[job_id][selectable] = None

                    if self.job_to_selectables_to_container_map[job_id][selectable] is not None:
                        self.logger.debug(f"Found container for selectable {selectable.get_label()}")
                        new_container_val = (
                            self.job_to_selectables_to_container_map[job_id][selectable].fetch_all_from_redis()
                        )

                        if new_container_val is None:
                            self.logger.debug(f"deleting container for selectable {selectable.get_label()}")
                            self.job_to_selectables_to_container_map[job_id][selectable].destroy_in_redis()

                        self.job_to_selectables_to_container_map[job_id][selectable] = new_container_val
                    else:
                        self.job_to_selectables_to_container_map[job_id][selectable] = (
                            self.get_latest_container_for_instance(
                                job_def_id=job_id,
                                job_instance_id=in_progress_instance.id
                            )
                        )
                        self.job_to_selectables_to_container_map[job_id][selectable].selectable \
                            = selectable

                # check for containers that are stale (job instances in DB not in progress)
                for selectable, container in self.job_to_selectables_to_container_map[job_id].items():
                    if container is not None:
                        if container.fetch_all_from_redis() is None or (
                                container.get_status() in StatusesEnum.get_terminal_statuses()
                        ):

                            self.job_to_selectables_to_container_map[job_id][selectable] = None
                            container.destroy_in_redis()

                to_return = self.job_to_selectables_to_container_map[job_id]
                self.logger.debug(f"get_containers_by_job_id: Returning {to_return}")

                return to_return
            else:
                if job_id not in self.non_selectables_to_container_map:
                    self.__cache_container_by_job_def(self.get_by_id(job_id, session=session))

                return self.non_selectables_to_container_map[job_id]

    def __cache_container_by_job_def(self, job_def: JobDefinitionImpl):
        """
        This method will cache the container for the job definition. It will be used to check if the job is already
        :param job_def:
        :param session:
        :return:
        """
        with self.dbm as dbm:
            session: Session = dbm.get_session()
            single_selectable_param_name = type(job_def).single_selectable_param_name()
            if single_selectable_param_name is not None:
                if job_def.id not in self.job_to_selectables_to_container_map:
                    self.job_to_selectables_to_container_map[job_def.id] = {}

                job_def.sync_single_selectable_data(session)
                self.job_to_selectables_to_container_map[job_def.id] = {
                    selectable: self.job_to_selectables_to_container_map[job_def.id].get(selectable, None)
                    for selectable in job_def.cached_selectables
                }
            else:
                if job_def.id not in self.non_selectables_to_container_map:
                    self.non_selectables_to_container_map[job_def.id] = None

    def get_by_id(self, id: int, session: Session) -> Optional[JobDefinitionImpl]:
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

    def get_latest_container_for_instance(self, job_instance_id: int, job_def_id: int) \
            -> Optional[VirtualJobProgressContainer]:
        # construct virtual prog container
        prog_container: VirtualJobProgressContainer = VirtualJobProgressContainer(
            job_instance_id=job_instance_id,
            job_definition_id=job_def_id
        )

        try:
            prog_container.use_redis(self.redis_client, prog_container.uuid).hydrate_from_redis()
            self.logger.debug(f"[glcfi] Found container for job instance {job_instance_id} with uuid {prog_container.uuid}")
            return prog_container
        except ContainerNotFoundError as e:
            self.logger.debug(f"[glcfi] Container not found for job instance {job_instance_id} with uuid {prog_container.uuid}")
            return None

    def run_job(
            self, *args, job_def: JobDefinitionImpl,
            parameter_values: Dict[str, Any] = None,
            selectable: Selectable = None,
            log_level: LogLevel = LogLevelsEnum.WARNING.value,
            **kwargs
    ):
        if parameter_values is None:
            parameter_values = {}

        with self.dbm as dbm:
            self.logger.debug(
                f"Running job {job_def.name}"
                f" with parameters {parameter_values}"
                f" or selectable {selectable.get_label() if selectable is not None else None}"
            )
            session: Session = dbm.get_session()
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

                latest_exec: JobInstance = job_class.get_latest_exec_for_selectable(selectable, session=session)
                if latest_exec is not None and latest_exec.end_time is None:
                    raise JobAlreadyRunningException(job_id=job_def.id)
            else:
                # todo
                if (
                        job_def.id in self.non_selectables_to_container_map
                        and self.non_selectables_to_container_map[job_def.id] is not None
                ):
                    raise JobAlreadyRunningException(job_id=job_def.id)

            current_instance = JobInstance()
            current_instance.job_definition_id = job_def.id
            current_instance.start_time = datetime.datetime.now()
            current_instance.date = current_instance.start_time
            current_instance.execution_status_id = StatusesEnum.PENDING.value.id
            current_instance.prerequisites_status_id = StatusesEnum.PENDING.value.id
            current_instance.completion_criteria_status_id = StatusesEnum.PENDING.value.id
            current_instance.set_status(StatusesEnum.PENDING)
            current_instance.parameters = json.dumps(parameter_values)
            self.save(current_instance, session=session)

            # todo: I don't like this flow - improve this
            current_instance.tooltip_id = current_instance.get_unique_id()

            job_progress_container: VirtualJobProgressContainer = VirtualJobProgressContainer(
                job_instance_id=current_instance.id,
                job_definition_id=job_def.id
            )

            job_progress_container.use_redis(self.redis_client, job_progress_container.uuid)
            job_progress_container.set_pending()

            if is_single_selectable:
                self.job_to_selectables_to_container_map[job_def.id][selectable] = job_progress_container
                job_progress_container.selectable = selectable
            else:
                self.non_selectables_to_container_map[job_def.id] = job_progress_container

            job_progress_container.start_time = current_instance.start_time
            job_progress_container.log_level = log_level
            job_progress_container.push_to_redis()

            self.redis_client: StrictRedis
            x = self.redis_client.exists(job_progress_container.uuid)
            if x == 0:
                self.logger.error(f"Could not find {job_progress_container.uuid} in redis")
            else:
                self.logger.debug(f"Found {job_progress_container.uuid} in redis")
                redis_data = pprint.pformat(self.redis_client.hgetall(job_progress_container.uuid))
                self.logger.debug(f"Redis data = {redis_data}")

            kwargs["prog_container_uuid"] = job_progress_container.uuid
            kwargs["parameter_values"] = parameter_values
            kwargs["job_def_id"] = job_def.id

            try:
                if current_instance in session:
                    # explicitly expunge the instance from the session instead of waiting for the session to close
                    # todo: do we still need this?
                    session.expunge(current_instance)

                celery_task_id = run_job.delay(**kwargs)
                self.logger.debug(f"result of celery execution = {celery_task_id}")

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
        try:
            with self.dbm.app.app_context():
                session: Session = self.dbm.get_session()
                self.logger.debug("checking prerequisites...")

                prerequisites_status: StatusesEnum = job_def.check_prerequisites(
                    *args, session=session, prog_container=prog_container,
                    parameter_values=parameter_values,
                    **kwargs
                )

                prog_container.prerequisites_status = prerequisites_status
                prog_container.last_status_updated_at = datetime.datetime.now()
                self.logger.debug(f"prerequisite status was {prerequisites_status}")

                if prerequisites_status in [StatusesEnum.WARNING, StatusesEnum.SUCCESS]:
                    self.logger.debug(f"executing job...")
                    execution_status: StatusesEnum = job_def.start(
                        *args, session=session, prog_container=prog_container,
                        parameter_values=parameter_values,
                        **kwargs
                    )

                    prog_container.execution_status = execution_status
                    prog_container.last_status_updated_at = datetime.datetime.now()
                    self.logger.debug(f"execution status was {execution_status}")

                    self.logger.debug(f"checking completion criteria...")

                    completion_criteria_status = job_def.check_completion_criteria(
                        *args, session=session, prog_container=prog_container,
                        parameter_values=parameter_values,
                        **kwargs
                    )

                    prog_container.completion_criteria_status = completion_criteria_status
                    prog_container.last_status_updated_at = datetime.datetime.now()

                    self.logger.debug(f"completion status was {completion_criteria_status}")
        except Exception as e:
            stacktrace = traceback.format_exc()
            prog_container.end_reason = str(e)
            prog_container.completion_criteria_status = StatusesEnum.FAILURE
            self.logger.error(f"Exception occurred: {stacktrace}")

        prog_container.end_time = datetime.datetime.now()
        prog_container.completed = True
        return prog_container


@shared_task
def run_job(
        *args,
        job_def_id: int,
        prog_container_uuid: str,
        parameter_values: Dict,
        **kwargs
):
    logger = logging.getLogger("celery-worker")
    logger.debug("Running job")
    # print thread and process id
    logger.debug(f"Thread id = {threading.get_ident()}")
    logger.debug(f"Process id = {os.getpid()}")

    from base_dash_app.application.runtime_application import RuntimeApplication
    dbm: DbManager = RuntimeApplication.get_instance().construct_dbm()
    redis_client = RuntimeApplication.get_instance().redis_client
    prog_container: VirtualJobProgressContainer = VirtualJobProgressContainer.get_from_redis_by_uuid(
        redis_client=redis_client,
        uuid=prog_container_uuid
    )

    with dbm as dbm:
        session: Session = dbm.new_session()
        session.expire_on_commit = False

        job_def = session.query(JobDefinition).filter_by(id=job_def_id).first()
        job_instance: JobInstance = session.query(JobInstance).filter_by(id=prog_container.job_instance_id).first()
        job_instance.set_status(StatusesEnum.IN_PROGRESS)
        session.commit()

        prog_container.set_in_progress()
        prog_container.push_to_redis()

        do_execution(
            *args,
            job_def=job_def,
            session=session,
            prog_container=prog_container,
            parameter_values=parameter_values,
            **kwargs
        )

        handle_completion(
            session=session,
            job_progress_container=prog_container
        )


def handle_completion(
        session: Session,
        job_progress_container: VirtualJobProgressContainer
):
    inner_session: Session = session
    job_instance_id = job_progress_container.job_instance_id

    job_instance = (
        inner_session.query(JobInstance)
        .filter_by(id=job_instance_id)
        .first()
    )

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

    try:
        inner_session.commit()
    except Exception as e:
        inner_session.rollback()
        raise e

    job_progress_container.destroy_in_redis()

    gc.collect()


def do_execution(
        *args,
        job_def: JobDefinition,
        prog_container: VirtualJobProgressContainer,
        session: Session,
        parameter_values: Dict,
        **kwargs
):
    logger = logging.getLogger(job_def.name or f"job_def_{prog_container.job_definition_id}")

    try:
        session.merge(job_def)

        logger.debug("checking prerequisites...")
        prerequisites_status: StatusesEnum = job_def.check_prerequisites(
            *args, session=session, prog_container=prog_container,
            parameter_values=parameter_values,
            **kwargs
        )

        prog_container.prerequisites_status = prerequisites_status
        prog_container.last_status_updated_at = datetime.datetime.now()
        prog_container.push_to_redis()
        logger.debug(f"prerequisite status was {prerequisites_status}")

        if prerequisites_status in [StatusesEnum.WARNING, StatusesEnum.SUCCESS]:
            logger.debug(f"executing job...")
            execution_status: StatusesEnum = job_def.start(
                *args, session=session, prog_container=prog_container,
                parameter_values=parameter_values,
                **kwargs
            )

            prog_container.execution_status = execution_status
            prog_container.last_status_updated_at = datetime.datetime.now()
            prog_container.push_to_redis()
            logger.debug(f"execution status was {execution_status}")

            logger.debug(f"checking completion criteria...")

            completion_criteria_status = job_def.check_completion_criteria(
                *args, session=session, prog_container=prog_container,
                parameter_values=parameter_values,
                **kwargs
            )

            prog_container.completion_criteria_status = completion_criteria_status
            prog_container.last_status_updated_at = datetime.datetime.now()
            prog_container.push_to_redis()

            logger.debug(f"completion status was {completion_criteria_status}")
    except Exception as e:
        stacktrace = traceback.format_exc()
        prog_container.end_reason = str(e)
        prog_container.completion_criteria_status = StatusesEnum.FAILURE
        prog_container.push_to_redis()
        logger.error(f"Exception occurred: {stacktrace}")
    finally:
        prog_container.end_time = datetime.datetime.now()
        logger.debug(f"end time = {prog_container.end_time}")

        logger.debug(f"status = {prog_container.get_status()}")

        prog_container.completed = True
        prog_container.push_to_redis()
        return prog_container
