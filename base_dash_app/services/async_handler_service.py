import concurrent
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, List, Callable, Any, Dict

from celery import Task

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService
from base_dash_app.virtual_objects.async_vos.work_containers import WorkContainer, WorkContainerGroup
from base_dash_app.virtual_objects.interfaces.startable import BaseWorkContainer


class AsyncWorkProgressContainer(WorkContainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.future: Optional[Future] = None


class AsyncGroupProgressContainer(WorkContainerGroup):

    def __init__(self, containers: List[BaseWorkContainer] = None):
        super().__init__(containers)
        self.futures: List[Future] = [
            container.future for container in self.work_containers
            if isinstance(container, AsyncWorkProgressContainer)
        ]

    def add_container(self, container: BaseWorkContainer):
        if container and isinstance(container, AsyncWorkProgressContainer):
            self.futures.append(container.future)

        super().add_container(container)


class AsyncTask(AsyncWorkProgressContainer):
    def __init__(
            self,
            work_func: Callable[[AsyncWorkProgressContainer, Any, Optional[Dict]], Any] = None,
            func_kwargs: Dict[str, Any] = None, task_name: str = None, is_hidden: bool = False
    ):
        super().__init__(is_hidden=is_hidden)
        self.work_func = work_func
        self.func_kwargs = func_kwargs or {}
        self.name = task_name
        # todo: think about done callbacks

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def start(self, task_input=None):
        super().start()
        try:
            self.work_func(self, task_input, self.func_kwargs)
        except Exception as e:
            stacktrace = traceback.format_exc()
            self.complete(
                status=StatusesEnum.FAILURE,
                status_message=str(e),
                stacktrace=stacktrace,
            )
            raise e


class AsyncOrderedTaskGroup(AsyncGroupProgressContainer, AsyncTask):
    def __init__(
            self, async_tasks: List[AsyncTask] = None,
            chain_results: bool = True,
            clear_intermediate_results: bool = True,
            task_group_title: str = None,
            require_all_success: bool = True,
    ):
        super().__init__(async_tasks)
        AsyncTask.__init__(self, work_func=self.start, task_name=task_group_title)
        self.chain_results = chain_results
        self.work_containers: List[AsyncTask] = async_tasks or []
        self.task_group_title = task_group_title
        self.clear_intermediate_results = clear_intermediate_results
        self.require_all_success = require_all_success

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def add_task(self, task: AsyncTask):
        if task is None:
            return

        self.add_container(task)

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None, stacktrace=None):
        for task in self.work_containers:
            if task.get_status() == StatusesEnum.PENDING or task.get_status() == StatusesEnum.IN_PROGRESS:
                task.complete(
                    result=result, status=status, progress=progress, status_message=status_message
                )

        WorkContainer.complete(
            self=self,
            result=result,
            status=status,
            progress=progress,
            status_message=status_message,
            stacktrace=stacktrace
        )

    def get_status_message(self):
        return self.status_message or WorkContainerGroup.get_status_message(self)

    def start(self, task_input=None):
        self.reset()
        in_failure_state = False
        first_failed_task = None

        if self.chain_results:
            prev_result = task_input
            for task in self.work_containers:
                if in_failure_state:
                    task.complete(status=StatusesEnum.FAILURE, status_message="Previous task failed")
                    continue

                try:
                    task.start(task_input=prev_result)
                    self.result = prev_result = task.get_result(clear_result=self.clear_intermediate_results)
                except Exception as e:
                    stacktrace = traceback.format_exc()
                    task.complete(status=StatusesEnum.FAILURE, status_message=str(e), stacktrace=stacktrace)
                    first_failed_task = task

                if task.get_status() == StatusesEnum.FAILURE and self.require_all_success:
                    in_failure_state = True
                    continue
        else:

            for task in self.work_containers:
                if in_failure_state:
                    task.complete(status=StatusesEnum.FAILURE, status_message="Previous task failed")
                    continue

                try:
                    task.start(task_input=task_input)
                    self.result = task.get_result(clear_result=self.clear_intermediate_results)
                except Exception as e:
                    stacktrace = traceback.format_exc()
                    task.complete(status=StatusesEnum.FAILURE, status_message=str(e), stacktrace=stacktrace)
                    first_failed_task = task

                if task.get_status() == StatusesEnum.FAILURE and self.require_all_success:
                    in_failure_state = True
                    continue

        num_success_message = f"{self.get_num_success()} / {len(self.work_containers)}"
        if in_failure_state:
            self.complete(
                status=StatusesEnum.FAILURE,
                status_message=f"{num_success_message} - {first_failed_task.name} failed"
            )
        else:
            self.complete(
                status=StatusesEnum.SUCCESS,
                status_message=f"{num_success_message} - {self.get_time_taken_message()}"
            )

    def get_result(self, clear_result=False) -> Any:
        return self.result


class AsyncUnorderedTaskGroup(WorkContainerGroup, AsyncTask):
    def __init__(
            self, async_service: 'AsyncHandlerService',
            async_tasks: List[AsyncTask] = None,
            task_group_title: str = None,
            reducer_func: Callable[[List[Any]], Any] = None,
            clear_intermediate_results: bool = True,
    ):
        super().__init__(async_tasks)
        AsyncTask.__init__(self, work_func=self.start, task_name=task_group_title)
        self.work_containers: List[AsyncTask] = async_tasks or []
        self.task_group_title = task_group_title
        self.async_service: 'AsyncHandlerService' = async_service
        if reducer_func is None:
            self.reducer_func = lambda x: [i for i in x]
        else:
            self.reducer_func = reducer_func

        self.clear_intermediate_results = clear_intermediate_results

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def get_status_message(self):
        return f"{self.status_message or WorkContainerGroup.get_status_message(self)}"

    def add_task(self, task: AsyncTask):
        if task is None:
            return

        self.add_container(task)

    def start(self, task_input=None):
        self.reset()

        for async_task in self.work_containers:
            self.async_service.submit_async_task(async_task, task_input=task_input)

        task_to_futures_map: Dict[AsyncTask, Future] = {task: task.future for task in self.work_containers}
        try:
            for future in concurrent.futures.as_completed(list(task_to_futures_map.values())):
                _ = future.result()

            self.complete(
                status=StatusesEnum.SUCCESS,
                status_message=WorkContainerGroup.get_status_message(self),
                result=self.reducer_func([
                    task.get_result(clear_result=self.clear_intermediate_results)
                    for task in self.work_containers
                ])
            )
        except Exception as e:
            # Cancel all the unstarted futures
            for task, future in task_to_futures_map.items():
                if not future.done():
                    future.cancel()
                    task.complete(
                        status=StatusesEnum.FAILURE, status_message="Aborted due to other task failure"
                    )

            self.complete(
                status=StatusesEnum.FAILURE,
                status_message=f"{self.get_num_success_message()} - {str(e)}",
                stacktrace=traceback.format_exc()
            )

    def get_result(self, clear_result=False) -> Any:
        return self.result

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None, stacktrace=None):
        for task in self.work_containers:
            if task.get_status() == StatusesEnum.PENDING or task.get_status() == StatusesEnum.IN_PROGRESS:
                task.complete(result=result, status=status, progress=progress, status_message=status_message)

        AsyncTask.complete(
            self=self,
            result=result,
            status=status,
            progress=progress,
            status_message=status_message,
            stacktrace=stacktrace
        )


class AsyncHandlerService(BaseService):
    def __init__(self, max_workers=5, **kwargs):
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

    def submit_async_task(self, async_task: AsyncTask, task_input=None):
        async_task.reset()
        async_task.future = self.threadpool_executor.submit(async_task.start, task_input=task_input)
        return async_task
