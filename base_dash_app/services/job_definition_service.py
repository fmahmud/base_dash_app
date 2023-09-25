import datetime
import gc
import json
import logging
import os
import pprint
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Type, Dict, Any, TypeVar

from celery import shared_task
from sqlalchemy.orm import Session

from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils.db_utils import DbManager
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

    def get_by_class(self, clazz):
        session: Session = self.dbm.get_session()
        job_def: JobDefinitionImpl = session.query(clazz).filter_by(job_class=clazz.__name__).first()
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
                # issue: (issue: 183): Handle checking for running job instance for non-SSP jobs
                pass

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

            job_progress_container.start_time = current_instance.start_time
            job_progress_container.log_level = log_level
            job_progress_container.push_to_redis()

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
    dbm: DbManager = RuntimeApplication.get_instance().get_dbm_by_pid()
    rta: RuntimeApplication = RuntimeApplication.get_instance()
    redis_client = rta.redis_client
    prog_container: VirtualJobProgressContainer = VirtualJobProgressContainer.from_redis(
        redis_client=redis_client,
        uuid=prog_container_uuid,
    )

    with dbm as dbm:
        session: Session = dbm.get_session()
        session.expire_on_commit = False

        job_def: JobDefinitionImpl = session.query(JobDefinition).filter_by(id=job_def_id).first()
        job_def.set_vars_from_kwargs(**rta.base_service_args)

        logger.debug(pprint.pformat(job_def.produce_kwargs()))

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
