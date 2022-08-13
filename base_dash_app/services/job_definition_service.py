import datetime
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Type, List, Dict

from sqlalchemy.orm import Session

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.models.job_definition import JobDefinition
from base_dash_app.models.job_instance import JobInstance
from base_dash_app.services.base_service import BaseService
from base_dash_app.virtual_objects.job_progress_container import VirtualJobProgressContainer
from base_dash_app.virtual_objects.result import Result

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]


class JobDefinitionService(BaseService):
    def __init__(self, *args, **kwargs):
        super().__init__(
            service_name="JobDefinitionService",
            object_type=JobDefinition,
            **kwargs
        )

        self.threadpool_executor = ThreadPoolExecutor(max_workers=5)

    def get_by_class(self, clazz):
        session: Session = self.dbm.get_session()
        job_def = session.query(clazz).filter_by(job_class=clazz.__name__).first()
        job_def.set_vars_from_kwargs(**self.produce_kwargs())
        return job_def

    def run_job(self, *args, job_def, parameter_values: Dict = None, **kwargs):
        if parameter_values is None:
            parameter_values = {}

        job_class = type(job_def)

        if not issubclass(job_class, JobDefinition):
            raise Exception(f"Provided job definition was not of a valid type. Was of type {job_class}.")

        if job_class == JobDefinition:
            raise Exception("Trying to execute a JobDefinition instead of a child class.")

        self.logger.info("Starting run job")
        if job_def.is_in_progress():
            raise Exception("Can't run two instances of the same job at the same time.")

        current_instance = JobInstance()
        current_instance.job_definition_id = job_def.id
        current_instance.start_time = datetime.datetime.now()
        current_instance.date = current_instance.start_time
        current_instance.completion_criteria_status_id = StatusesEnum.IN_PROGRESS.value.id
        current_instance.parameters = json.dumps(parameter_values)
        self.save(current_instance)

        # todo: I don't like this flow - improve this
        current_instance.tooltip_id = current_instance.get_unique_id()

        kwargs["job_instance"] = current_instance
        kwargs["job_def"] = job_def

        job_progress_container: VirtualJobProgressContainer = VirtualJobProgressContainer(
            job_instance_id=current_instance.id,
            job_definition_id=job_def.id
        )

        job_def.current_prog_container = job_progress_container

        kwargs["prog_container"] = job_progress_container
        kwargs["parameter_values"] = parameter_values

        def handle_completion(future):
            current_instance.progress = job_progress_container.progress
            current_instance.end_time = job_progress_container.end_time
            current_instance.execution_status_id = job_progress_container.execution_status.value.id
            current_instance.completion_criteria_status_id = job_progress_container.completion_criteria_status.value.id
            current_instance.prerequisites_status_id = job_progress_container.prerequisites_status.value.id
            current_instance.end_reason = job_progress_container.end_reason
            current_instance.resultable_value = job_progress_container.result
            current_instance.result = Result(
                job_progress_container.result, job_progress_container.completion_criteria_status
            )
            current_instance.extras = json.dumps(job_progress_container.extras)
            current_instance.logs = json.dumps(job_progress_container.logs)

            self.save(current_instance)
            job_def.process_cached_result(current_instance)
            job_def.current_prog_container = None

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
            self.logger.info(f"Using new session: {session.hash_key}")

            self.logger.info("checking prerequisites...")

            prerequisites_status: StatusesEnum = job_def.check_prerequisites(
                *args, session=session, prog_container=prog_container,
                parameter_values=parameter_values,
                **kwargs
            )

            prog_container.prerequisites_status = prerequisites_status
            self.logger.info(f"prerequisite status was {prerequisites_status}")

            if prerequisites_status in [StatusesEnum.WARNING, StatusesEnum.SUCCESS]:
                self.logger.info(f"executing job...")
                execution_status: StatusesEnum = job_def.start(
                    *args, session=session, prog_container=prog_container,
                    parameter_values=parameter_values,
                    **kwargs
                )

                prog_container.execution_status = execution_status
                self.logger.info(f"execution status was {execution_status}")

                self.logger.info(f"checking completion criteria...")

                completion_criteria_status = job_def.check_completion_criteria(
                    *args, session=session, prog_container=prog_container,
                    parameter_values=parameter_values,
                    **kwargs
                )

                prog_container.completion_criteria_status = completion_criteria_status

                self.logger.info(f"completion status was {completion_criteria_status}")
        except Exception as e:
            prog_container.end_reason = str(e)
            prog_container.completion_criteria_status = StatusesEnum.FAILURE
        finally:
            prog_container.end_time = datetime.datetime.now()
            self.logger.info(f"end time = {prog_container.end_time}")

            self.logger.info(f"status = {prog_container.get_status()}")

            prog_container.completed = True
            session.close()
            return prog_container

