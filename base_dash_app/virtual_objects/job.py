import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from abc import abstractmethod, ABC
from typing import Callable, Optional, List

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.startable import Startable
from base_dash_app.virtual_objects.interfaces.stoppable import Stoppable
from base_dash_app.virtual_objects.interfaces.progressable import Progressable
from base_dash_app.virtual_objects.interfaces.resultable import Resultable
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent
from base_dash_app.virtual_objects.interfaces.resultable_event_series import ResultableEventSeries
from base_dash_app.virtual_objects.result import Result

num_instances = 0
threadpool_executor = ThreadPoolExecutor(max_workers=5)
passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]


class JobProgressContainer:
    def __init__(self):
        self.progress = 0
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.prerequisites_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.completion_criteria_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.end_reason = None
        self.extras = {}

    def get_status(self):
        if self.prerequisites_status in passing_statuses:
            if self.execution_status in passing_statuses:
                return self.completion_criteria_status
            else:
                return self.execution_status
        else:
            return self.prerequisites_status


class JobDefinition(ResultableEventSeries, Startable, Stoppable, ABC):
    def __init__(self, job_name: str):
        ResultableEventSeries.__init__(self)
        Startable.__init__(self)
        Stoppable.__init__(self)

        global num_instances
        self.job_name: str = job_name
        num_instances += 1

        self.job_id: int = num_instances
        self.__progress_bar_id = f"job-progress-bar-id-{self.job_id}"
        self.__current_thread = None
        self.__current_job_instance: Optional[JobInstance] = None
        self.logger = logging.getLogger(self.job_name)

    def is_in_progress(self):
        return self.__current_job_instance is not None

    def get_progress(self):
        if self.is_in_progress():
            return self.__current_job_instance.get_progress()

    @abstractmethod
    def check_completion_criteria(self, *args, progress_container: JobProgressContainer, **kwargs) -> StatusesEnum:
        pass

    @abstractmethod
    def check_prerequisites(self, *args, progress_container: JobProgressContainer, **kwargs) -> StatusesEnum:
        pass
    
    @abstractmethod
    def start(
        self, *args,
        progress_container: JobProgressContainer,
        **kwargs
    ):
        pass

    @abstractmethod
    def stop(self, *args, progress_container: JobProgressContainer, **kwargs):
        pass

    def done(self):
        self.__current_thread = None
        self.__current_job_instance = None

    def run_job(self, *args, **kwargs):
        global threadpool_executor

        if self.__current_thread is not None or self.__current_job_instance is not None:
            raise Exception("Can't run two instances of the same job at the same time")

        self.__current_job_instance = JobInstance(self, len(self.events) + 1)
        try:
            self.__current_thread = threadpool_executor.submit(
                self.__current_job_instance.start, *args, **kwargs
            )
        except Exception as e:
            raise e


class JobInstance(Startable, Stoppable, ResultableEvent, Progressable):
    def get_progress(self):
        return self.progress_container.progress

    def __init__(self, job_definition: JobDefinition, instance_id: int):
        Startable.__init__(self)
        Stoppable.__init__(self)
        ResultableEvent.__init__(self, datetime.datetime.now())

        self.job_definition: JobDefinition = job_definition
        self.result_value: float = 0.0
        self.status: StatusesEnum = StatusesEnum.PENDING
        self.instance_id = instance_id
        self.progress_container = JobProgressContainer()
        self.start_time = None
        self.end_time = None

    def __hash__(self):
        return hash(self.job_definition.job_id)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.instance_id == other.instance_id and self.job_definition is other.job_definition

    def get_result(self, *, perspective: Callable[['Resultable'], Optional[int]] = None) -> Result:
        return Result(self.result_value, self.status)

    def get_status_color(self, *, perspective=None) -> StatusesEnum:
        return self.status

    def get_name(self):
        return f"{self.job_definition.job_name} - {self.instance_id}"

    def get_header(self) -> (str, dict):
        return self.get_name(), {}

    def get_text(self) -> (str, dict):
        pass

    def get_extras(self):
        pass

    def get_link(self) -> str:
        pass

    def start(self, *args, **kwargs):
        try:
            self.start_time = datetime.datetime.now()
            self.status = StatusesEnum.IN_PROGRESS
            self.progress_container.prerequisites_status = self.job_definition.check_prerequisites(
                *args, progress_container=self.progress_container, **kwargs
            )

            if self.progress_container.prerequisites_status in [StatusesEnum.WARNING, StatusesEnum.SUCCESS]:
                self.progress_container.execution_status = self.job_definition.start(
                    *args, progress_container=self.progress_container, **kwargs
                )

                self.progress_container.completion_criteria_status = self.job_definition.check_completion_criteria(
                    *args, progress_container=self.progress_container, **kwargs
                )
        except Exception as e:
            self.progress_container.end_reason = e
            raise e
        finally:
            self.end_time = datetime.datetime.now()
            self.result_value = (self.end_time - self.start_time).total_seconds()
            self.status = self.progress_container.get_status()
            self.job_definition.process_result(self.get_result(), self)
            self.job_definition.done()

    def stop(self, *args, **kwargs):
        return self.job_definition.stop(*args, **kwargs)
