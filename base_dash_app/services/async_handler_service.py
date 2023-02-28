import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, List, Callable, Any, Dict, Tuple

from base_dash_app.enums.log_levels import LogLevel, LogLevelsEnum
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService


class AsyncWorkProgressContainer:
    def __init__(self):
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.future = None
        self.status_message = ""

    def set_status_message(self, status_message: str):
        self.status_message = status_message

    def start(self):
        self.start_time = datetime.datetime.now()
        self.execution_status = StatusesEnum.IN_PROGRESS
        self.progress = 0

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100):
        self.end_time = datetime.datetime.now()
        self.execution_status = status
        self.result = result
        self.progress = progress


class AsyncGroupProgressContainer:
    def __init__(self, containers: List[AsyncWorkProgressContainer] = None):
        self.async_work_progress_containers: List[AsyncWorkProgressContainer] = containers or []
        self.futures: List[Future] = [container.future for container in self.async_work_progress_containers]

    def get_status_messages(self):
        return [container.status_message for container in self.async_work_progress_containers]

    def get_start_time(self):
        return None if len(self.async_work_progress_containers) == self.get_num_pending() else \
            min([container.start_time for container in self.async_work_progress_containers])

    def get_end_time(self):
        return None if self.get_num_in_progress() > 0 else \
            max([container.end_time for container in self.async_work_progress_containers])

    def add_container(self, container: AsyncWorkProgressContainer):
        if container is None:
            return

        self.async_work_progress_containers.append(container)
        self.futures.append(container.future)

    def add_all_containers(self, containers: List[AsyncWorkProgressContainer]):
        if containers is None:
            return

        self.async_work_progress_containers.extend(containers)
        self.futures.extend([container.future for container in containers])

    def get_progress(self):
        total_progress = sum(
            [container.progress for container in self.async_work_progress_containers]
        )

        return total_progress / len(self.async_work_progress_containers)

    def get_num_by_status(self, status: StatusesEnum):
        return len(
            [
                container
                for container in self.async_work_progress_containers
                if container.execution_status == status
            ]
        )

    def get_num_pending(self):
        return self.get_num_by_status(StatusesEnum.PENDING)

    def get_num_in_progress(self):
        return self.get_num_by_status(StatusesEnum.IN_PROGRESS)

    def get_num_success(self):
        return self.get_num_by_status(StatusesEnum.SUCCESS)

    def get_num_failed(self):
        return self.get_num_by_status(StatusesEnum.FAILED)


class AsyncTask:
    def __init__(
            self,
            work_func: Callable[[AsyncWorkProgressContainer, Any, Optional[Dict]], Any],
            async_container: AsyncWorkProgressContainer = None,
            func_kwargs: Dict[str, Any] = None,
    ):
        self.work_func = work_func
        self.async_container = async_container
        self.func_kwargs = func_kwargs or {}

    def set_async_container(self, async_container: AsyncWorkProgressContainer):
        self.async_container = async_container

    def start(self, task_input=None):
        self.work_func(self.async_container, task_input, self.func_kwargs)


class AsyncOrderedTaskGroup:
    def __init__(
            self,
            async_group_container: AsyncGroupProgressContainer,
            async_tasks: List[AsyncTask] = None,
            chain_results: bool = True,
    ):
        if async_group_container is None:
            raise ValueError('async_group_container cannot be None')

        self.async_tasks = async_tasks or []
        self.async_group_container = async_group_container
        self.chain_results = chain_results
        self.future: Optional[Future] = None

    def get_latest_status_message(self):
        messages = [
            message for message in self.async_group_container.get_status_messages()
            if message not in (None, "")
        ]

        if len(messages) == 0:
            return "Initializing..."

        return messages[-1]

    def add_task(self, task: AsyncTask):
        if task is None:
            return

        if task.async_container is None:
            task.set_async_container(AsyncWorkProgressContainer())

        self.async_tasks.append(task)
        self.async_group_container.add_container(task.async_container)

    def add_all_tasks(self, tasks: List[AsyncTask]):
        if tasks is None:
            return

        for task in tasks:
            self.add_task(task)

    def start(self):
        if self.chain_results:
            prev_result = None
            for task in self.async_tasks:
                task.start(task_input=prev_result)
                prev_result = task.async_container.result
        else:
            for task in self.async_tasks:
                task.start()


class AsyncHandlerService(BaseService):
    def __init__(self, max_workers=10, **kwargs):
        super().__init__(**kwargs)

        self.threadpool_executor = ThreadPoolExecutor(max_workers=max_workers)

    def do_work(self, func, done_callback=None, *args, **kwargs):

        async_container: AsyncWorkProgressContainer = AsyncWorkProgressContainer()
        kwargs['async_container'] = async_container

        if done_callback is None:
            async_container.future = self.threadpool_executor.submit(func, *args, **kwargs)
        else:
            async_container.future = (
                self.threadpool_executor
                .submit(func, *args, **kwargs)
                .add_done_callback(done_callback)
            )

        return async_container

    def submit_async_ordered_task_group(self, aotg: AsyncOrderedTaskGroup, done_callback=None):
        if done_callback is None:
            aotg.future = self.threadpool_executor.submit(aotg.start)
        else:
            aotg.future = (
                self.threadpool_executor
                .submit(aotg.start)
                .add_done_callback(done_callback)
            )

        return aotg




