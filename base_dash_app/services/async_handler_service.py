import datetime
from concurrent.futures import ThreadPoolExecutor, Future, wait
from typing import Optional, List, Callable, Any, Dict

from dash import html

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.interfaces.startable import BaseWorkContainer, BaseWorkContainerGroup
import dash_bootstrap_components as dbc


class WorkContainer(BaseWorkContainer, BaseComponent):
    def __init__(self, name: str = None, color: str = "primary"):
        super().__init__()

        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = None
        self.start_time = None
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.status_message = ""
        self.name = name
        self.color = color

    def get_name(self):
        return self.name

    def set_progress(self, progress: float):
        self.progress = progress

    def set_status_message(self, status_message: str):
        self.status_message = status_message

    def start(self):
        self.start_time = datetime.datetime.now()
        self.execution_status = StatusesEnum.IN_PROGRESS
        self.progress = 0

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None):
        self.end_time = datetime.datetime.now()
        self.execution_status = status
        self.result = result
        self.progress = progress
        self.status_message = f"""Done in {
        date_utils.readable_time_since(start_time=self.start_time, end_time=self.end_time)
        }"""

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def get_progress(self):
        return self.progress

    def get_status_message(self):
        return self.status_message

    def get_status(self) -> StatusesEnum:
        return self.execution_status

    def get_result(self) -> Any:
        return self.result

    def render(self):
        return html.Div(
            children=[
                html.H4(self.get_name(), style={"float": "left"}),
                html.Pre(self.get_status_message(),
                         style={
                             "position": "relative",
                             "float": "right",
                             "marginBottom": "0px",
                         },
                         ) if self.get_status_message() else None,
                dbc.Progress(
                    value=self.get_progress(),
                    label=self.get_progress_label(),
                    color=self.color,
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
                "marginBottom": "20px",
            },
        )


class WorkContainerGroup(BaseWorkContainerGroup, BaseComponent):
    def __init__(self, containers: List[WorkContainer] = None, name: str = None, color: str = "primary"):
        self.work_containers: List[WorkContainer] = containers or []
        self.name = name
        self.color = color

    def get_name(self):
        return self.name

    def get_status_message(self) -> str:
        # return message saying how many successfully done
        num_success = f"""{self.get_num_success()} / {len(self.work_containers)} """
        if self.get_num_in_progress() > 0 or self.get_num_pending() > 0:
            return f"{num_success} - {self.get_latest_status_message() or ''}"

        return f"Done in " \
               f"{date_utils.readable_time_since(start_time=self.get_start_time(), end_time=self.get_end_time())}"

    def set_progress(self, progress: float):
        pass

    def complete(self, *args, **kwargs):
        pass

    def get_status(self):
        if len(self.work_containers) == 0:
            return StatusesEnum.PENDING

        if len(self.work_containers) == self.get_num_pending():
            return StatusesEnum.PENDING

        if self.get_num_in_progress() > 0:
            return StatusesEnum.IN_PROGRESS

        if self.get_num_failed() > 0:
            return StatusesEnum.FAILED

        return StatusesEnum.SUCCESS

    def get_status_messages(self):
        return [
            container.get_status_message() for container in self.work_containers
        ]

    def get_start_time(self):
        return None if len(self.work_containers) == self.get_num_pending() else \
            min([container.get_start_time() for container in self.work_containers])

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
    def __init__(self):
        super().__init__()
        self.future = None


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
            func_kwargs: Dict[str, Any] = None, task_name: str = None
    ):
        super().__init__()
        self.work_func = work_func
        self.func_kwargs = func_kwargs or {}
        self.name = task_name
        # todo: think about done callbacks

    def start(self, task_input=None):
        super().start()
        try:
            self.work_func(self, task_input, self.func_kwargs)
        except Exception as e:
            print(e)


class AsyncOrderedTaskGroup(AsyncGroupProgressContainer, AsyncTask):
    def __init__(
            self, async_tasks: List[AsyncTask] = None,
            chain_results: bool = True,
            task_group_title: str = None
    ):
        super().__init__(async_tasks)
        AsyncTask.__init__(self, work_func=self.start, task_name=task_group_title)
        self.chain_results = chain_results
        self.work_containers: List[AsyncTask] = async_tasks or []
        self.task_group_title = task_group_title

    def add_task(self, task: AsyncTask):
        if task is None:
            return

        self.add_container(task)

    def start(self, task_input=None):
        if self.chain_results:
            prev_result = task_input
            for task in self.work_containers:
                task.start(task_input=prev_result)
                prev_result = task.get_result()
        else:
            prev_result = task_input
            for task in self.work_containers:
                task.start(prev_result)
                prev_result = None

    def get_result(self) -> Any:
        if len(self.work_containers) == 0:
            return None
        return self.work_containers[-1].result


class AsyncUnorderedTaskGroup(WorkContainerGroup, AsyncTask):
    def __init__(
            self, async_service: 'AsyncHandlerService',
            async_tasks: List[AsyncTask] = None,
            task_group_title: str = None,
            reducer_func: Callable[[List[Any]], Any] = None
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

    def add_task(self, task: AsyncTask):
        if task is None:
            return

        self.add_container(task)

    def start(self, task_input=None):
        for async_task in self.work_containers:
            self.async_service.submit_async_task(async_task, task_input=task_input)

        futures = [task.future for task in self.work_containers]
        wait(futures)

    def get_result(self) -> Any:
        if len(self.work_containers) == 0:
            return None

        return self.reducer_func([task.get_result() for task in self.work_containers])


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

    def submit_async_task(self, async_task: AsyncTask, task_input=None):
        async_task.future = self.threadpool_executor.submit(async_task.start, task_input=task_input)
        return async_task
