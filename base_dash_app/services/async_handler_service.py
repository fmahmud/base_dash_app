import concurrent
import datetime
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, Future, wait, FIRST_EXCEPTION
from typing import Optional, List, Callable, Any, Dict

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.interfaces.startable import BaseWorkContainer, BaseWorkContainerGroup
import dash_bootstrap_components as dbc


class WorkContainer(BaseWorkContainer, BaseComponent):
    def __init__(self, name: str = None, color: str = "primary", is_hidden: bool = False, *args, **kwargs):
        super().__init__()
        BaseComponent.__init__(self, *args, **kwargs)

        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.stacktrace = None
        self.progress: float = 0.0
        self.status_message = None
        self.name = name
        self.color = color
        self.is_hidden = is_hidden

    def reset(self):
        self.execution_status = StatusesEnum.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.stacktrace = None
        self.progress = 0.0
        self.status_message = None

    def get_name(self):
        return self.name

    def set_progress(self, progress: float):
        self.progress = progress

    def set_status_message(self, status_message: str):
        if status_message:
            self.status_message = status_message

    def start(self):
        self.start_time = datetime.datetime.now()
        self.execution_status = StatusesEnum.IN_PROGRESS
        self.progress = 0
        self.result = None

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None, stacktrace=None):
        self.end_time = datetime.datetime.now()
        self.execution_status = status
        self.stacktrace = stacktrace

        if result is not None:
            self.result = result

        self.set_progress(progress=progress)
        self.set_status_message(
            status_message=status_message or self.get_time_taken_message()
        )

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def get_progress(self):
        return self.progress

    def get_status_message(self):
        return self.status_message

    def get_time_taken_message(self):
        return f"""Done in {
            date_utils.readable_time_since(start_time=self.get_start_time(), end_time=self.get_end_time())
        }"""

    def get_status(self) -> StatusesEnum:
        return self.execution_status

    def get_result(self, clear_result=False) -> Any:
        to_return = self.result
        if clear_result:
            self.result = None
        return to_return

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def render(self):
        if self.is_hidden:
            return None

        status_message_id = f"{self.id}-status-message"

        return html.Div(
            children=[
                html.Div(
                    self.get_name(),
                    style={
                        "float": "left", "fontSize": "18px",
                        "maxWidth": "50%", "textOverflow": "ellipsis",
                    }),
                html.Pre(
                    self.get_status_message(),
                    style={
                        "position": "relative",
                        "float": "right",
                        "marginBottom": "0px",
                        "maxWidth": "50%",
                        "textOverflow": "ellipsis",
                     },
                    id=status_message_id,
                ) if self.get_status_message() else None,
                dbc.Tooltip(
                    self.get_status_message(),
                    target=status_message_id,
                    placement="right",
                    id=f"{self.id}-status-message-tooltip",
                ),
                dbc.Progress(
                    value=self.get_progress(),
                    label=self.get_progress_label(),
                    color=self.get_status().value.hex_color,
                    animated=self.get_status() == StatusesEnum.IN_PROGRESS,
                    striped=self.get_status() == StatusesEnum.IN_PROGRESS,
                    style={
                        "position": "relative",
                        "float": "right",
                        "width": "100%",
                    },
                ),
            ],
            style={
                "position": "relative",
                "float": "left",
                "width": "100%",
                "height": "50px",
                "marginBottom": "10px",
            },
        )


class WorkContainerGroup(BaseWorkContainerGroup, BaseComponent):
    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None):
        pass

    def __init__(self, containers: List[WorkContainer] = None, name: str = None, color: str = "primary"):
        super().__init__()
        BaseComponent.__init__(self)
        self.work_containers: List[WorkContainer] = containers or []
        self.name = name
        self.color = color

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def reset(self):
        [container.reset() for container in self.work_containers]

    def get_name(self):
        return self.name

    def get_num_success_message(self):
        return f"{self.get_num_success()} / {len(self.work_containers)}"

    def get_status_message(self) -> str:
        # return message saying how many successfully done
        num_success = self.get_num_success_message()
        message = f"{num_success}"
        status = self.get_status()

        if status == StatusesEnum.PENDING:
            message += " - Not Started"
        elif status == StatusesEnum.IN_PROGRESS:
            message += f" - {self.get_latest_status_message() or ''}"
        elif status == StatusesEnum.SUCCESS:
            message = f"{self.get_num_success()} Done in" \
               f" {date_utils.readable_time_since(start_time=self.get_start_time(), end_time=self.get_end_time())}"
        elif status == StatusesEnum.FAILURE:
            failure_containers = [
                container for container in self.work_containers
                if container.get_status() == StatusesEnum.FAILURE
            ]
            message = f"{len(failure_containers)} / {len(self.work_containers)} - Failed"
        else:
            raise ValueError(f"Unknown status: {status}")

        return message

    def set_progress(self, progress: float):
        pass

    def get_status(self):
        if len(self.work_containers) == 0:
            return StatusesEnum.PENDING

        if len(self.work_containers) == self.get_num_pending():
            return StatusesEnum.PENDING

        if self.get_num_failed() > 0:
            return StatusesEnum.FAILURE

        if self.get_num_in_progress() > 0:
            return StatusesEnum.IN_PROGRESS

        return StatusesEnum.SUCCESS

    def get_status_messages(self):
        return [
            container.get_status_message() for container in self.work_containers if not container.is_hidden
        ]

    def get_start_time(self):
        if len(self.work_containers) == self.get_num_pending():
            return None
        else:
            start_times = [
                container.get_start_time() for container in self.work_containers
                if container.get_start_time() is not None
            ]

            if len(start_times) == 0:
                return None

            return min(start_times)

    def get_end_time(self):
        return None if self.get_num_in_progress() > 0 else \
            max([container.get_end_time() for container in self.work_containers])

    def get_progress(self):
        total_progress = sum(
            [container.get_progress() for container in self.work_containers]
        )

        return total_progress / len(self.work_containers)

    def get_num_by_status(self, status: StatusesEnum):
        return len(
            [
                container
                for container in self.work_containers
                if container.get_status() == status
            ]
        )

    def add_container(self, container: WorkContainer):
        if container is None:
            return

        self.work_containers.append(container)

    def add_all_containers(self, containers: List[WorkContainer]):
        if containers is None:
            return

        self.work_containers.extend(containers)

    def get_num_pending(self):
        return self.get_num_by_status(StatusesEnum.PENDING)

    def get_num_in_progress(self):
        return self.get_num_by_status(StatusesEnum.IN_PROGRESS)

    def get_num_success(self):
        return self.get_num_by_status(StatusesEnum.SUCCESS)

    def get_num_failed(self):
        return self.get_num_by_status(StatusesEnum.FAILURE)

    def get_latest_status_message(self):
        messages = [
            message for message in self.get_status_messages()
            if message not in (None, "")
        ]

        if len(messages) == 0:
            return "Initializing..."

        return messages[-1]

    def render(self):
        return html.Div(
            children=[
                WorkContainer.render(container)
                for container in self.work_containers
            ],
            style={
                "width": "100%", "height": "100%",
                "display": "fixed",
            },
        )


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
            self, work_func: Callable[[AsyncWorkProgressContainer, Any, Optional[Dict]], Any] = None,
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
