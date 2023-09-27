import datetime
import json
from typing import Optional, Any, List, Dict

import dash_bootstrap_components as dbc
from dash import html
from redis import StrictRedis

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.abstract_redis_dto import AbstractRedisDto
from base_dash_app.virtual_objects.interfaces.startable import BaseWorkContainer, BaseWorkContainerGroup


class WorkContainer(BaseWorkContainer, BaseComponent, AbstractRedisDto):
    def __init__(
            self, name: str = None,
            color: str = "primary",
            is_hidden: bool = False,
            *args, **kwargs
    ):
        super().__init__()
        BaseComponent.__init__(self, *args, **kwargs)
        AbstractRedisDto.__init__(self, *args, **kwargs)

        self.execution_status: Optional[StatusesEnum] = StatusesEnum.NOT_STARTED
        self.result = None
        self.start_time = None
        self.end_time = None
        self.stacktrace = None
        self.progress: float = 0.0
        self.status_message = None
        self.name = name
        self.color = color
        self.is_hidden = is_hidden

    def reset(self, destroy_in_redis=False):
        self.execution_status = StatusesEnum.NOT_STARTED
        self.result = None
        self.start_time = None
        self.end_time = None
        self.stacktrace = None
        self.progress = 0.0
        self.status_message = None
        if destroy_in_redis:
            self.destroy_in_redis()

    def to_dict(self):
        return {
            "execution_status": (
                self.execution_status.value.name if self.execution_status else StatusesEnum.NOT_STARTED.value.name
            ),
            "result": json.dumps(self.result) if self.result else "",
            "start_time":  datetime.datetime.strftime(
                self.start_time, date_utils.STANDARD_DATETIME_FORMAT
            ) if self.start_time else "",
            "end_time": datetime.datetime.strftime(
                self.end_time, date_utils.STANDARD_DATETIME_FORMAT
            ) if self.end_time else "",
            "stacktrace": str(self.stacktrace) if self.stacktrace else "",
            "progress": self.progress or 0,
            "status_message": self.status_message or "",
            "name": self.name,
            "is_hidden": str(self.is_hidden),
            "type": "WorkContainer",
            "uuid": self.uuid,
        }

    def from_dict(self, d: Dict[str, str]):
        # make sure no changes from this function are propagated to redis
        previous_readonly_value = self.read_only
        self.set_read_only()

        self.name = d.get("name", "")

        self.execution_status = (
            StatusesEnum.get_by_name(
                d.get("execution_status", StatusesEnum.NOT_STARTED.value.name)
            )
        )

        self.result = d.get("result", "")
        # print result
        self.result = json.loads(self.result) if self.result != "" else None

        self.set_start_time_from_string(d.get("start_time", ""))
        self.set_end_time_from_string(d.get("end_time", ""))

        self.stacktrace = d.get("stacktrace", "")
        self.progress = float(d.get("progress", 0)) if d.get("progress", 0) != "" else 0
        self.status_message = d.get("status_message", "")
        self.is_hidden = d.get("is_hidden", "False") == "True"
        self.color = d.get("color", "red")

        # set it back to what it was before
        self.set_read_only(previous_readonly_value)

    def get_name(self):
        return self.name

    def set_progress(self, progress: float):
        self.progress = progress
        self.set_value_in_redis("progress", str(progress))

    def set_status_message(self, status_message: str):
        if status_message:
            self.status_message = status_message
            self.set_value_in_redis("status_message", status_message)

    def set_status(self, status: StatusesEnum):
        self.execution_status = status or StatusesEnum.NOT_STARTED
        self.set_value_in_redis("execution_status", self.execution_status.value.name)

    def set_start_time_from_string(self, start_time_str):
        if start_time_str in ["", None]:
            self.start_time = None
        else:
            self.start_time = datetime.datetime.strptime(
                start_time_str, date_utils.STANDARD_DATETIME_FORMAT
            )

    def set_end_time_from_string(self, end_time_str):
        if end_time_str in ["", None]:
            self.end_time = None
        else:
            self.end_time = datetime.datetime.strptime(
                end_time_str, date_utils.STANDARD_DATETIME_FORMAT
            )

    def set_start_time(self, start_time: datetime.datetime):
        self.start_time = start_time

        if self.start_time is None:
            self.set_value_in_redis("start_time", "")
        else:
            self.set_value_in_redis("start_time", datetime.datetime.strftime(
                self.start_time, date_utils.STANDARD_DATETIME_FORMAT
            ))

    def set_end_time(self, end_time: datetime.datetime):
        self.end_time = end_time

        if self.end_time is None:
            self.set_value_in_redis("end_time", "")
        else:
            self.set_value_in_redis("end_time", datetime.datetime.strftime(
                self.end_time, date_utils.STANDARD_DATETIME_FORMAT
            ))

    def set_result(self, result: Any):
        self.result = result
        dumped_string = json.dumps(result)
        self.set_value_in_redis("result", dumped_string)

    def set_stacktrace(self, stacktrace: str):
        self.stacktrace = stacktrace
        self.set_value_in_redis("stacktrace", stacktrace)

    def start(self):
        self.set_start_time(datetime.datetime.now())
        self.set_status(StatusesEnum.IN_PROGRESS)
        self.set_progress(progress=0.0)
        self.set_result(result={})

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None, stacktrace=None):
        self.set_end_time(datetime.datetime.now())
        self.set_status(status=status)
        self.set_progress(progress=progress)
        self.set_stacktrace(stacktrace=stacktrace)
        self.set_progress(progress=progress)
        self.set_status_message(
            status_message=status_message or self.get_time_taken_message()
        )

        if result is not None:
            self.set_result(result=result)

    def get_start_time(self, with_refresh=False):
        if with_refresh:
            str_val = self.get_value_from_redis("start_time")
            if str_val == "" or str_val is None:
                self.start_time = None
            else:
                self.start_time = datetime.datetime.strptime(
                    str_val, date_utils.STANDARD_DATETIME_FORMAT
                )
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
                    animated=self.get_status() in StatusesEnum.get_non_terminal_statuses(),
                    striped=self.get_status() in StatusesEnum.get_non_terminal_statuses(),
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


class WorkContainerGroup(BaseWorkContainerGroup, BaseComponent, AbstractRedisDto):
    def from_dict(self, data: dict):
        self.work_containers = []
        for container_uuid in json.loads(data["work_containers"]):
            container = (
                WorkContainer()
                .use_redis(redis_client=self.redis_client, uuid=container_uuid)
                .hydrate_from_redis()
            )

            self.work_containers.append(container)

        self.name = data["name"]
        self.color = data["color"] or ""

    def to_dict(self) -> dict:
        return {
            "work_containers": json.dumps([container.uuid for container in self.work_containers]),
            "name": self.name or "",
            "color": self.color or "",
            "type": "WorkContainerGroup",
            "error": "True" if self.get_status() == StatusesEnum.FAILURE else "False",
        }

    def get_container_by_uuid(self, uuid: str) -> Optional[WorkContainer]:
        for container in self.work_containers:
            if container.uuid == uuid:
                return container
        return None

    def refresh_all(self):
        for container in self.work_containers:
            if isinstance(container, WorkContainerGroup):
                container.refresh_all()
            else:
                container.fetch_all_from_redis()

    def use_redis(self, redis_client: StrictRedis, uuid: str):
        super().use_redis(redis_client, uuid)
        for container in self.work_containers:
            container.use_redis(redis_client, container.uuid)

        return self

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None):
        pass

    def __init__(
            self,
            containers: List[WorkContainer] = None,
            name: str = None,
            color: str = "primary",
            **kwargs
    ):
        super().__init__(**kwargs)
        BaseComponent.__init__(self, **kwargs)
        AbstractRedisDto.__init__(self, **kwargs)
        self.work_containers: List[WorkContainer] = containers or []
        self.name = name
        self.color = color

    def __repr__(self):
        return f"[{self.__class__.__name__}]-{self.name}-{self.id}"

    def clear(self, destroy_in_redis=False):
        if destroy_in_redis:
            [container.destroy_in_redis() for container in self.work_containers]
            self.destroy_in_redis()
        self.work_containers.clear()

    def reset(self, destroy_in_redis=False):
        [container.reset(destroy_in_redis) for container in self.work_containers]
        if destroy_in_redis:
            self.destroy_in_redis()

    def get_name(self):
        return self.name

    def get_num_success_message(self):
        return f"{self.get_num_success()} / {len(self.work_containers)}"

    def get_status_message(self) -> str:
        # return message saying how many successfully done
        num_success = self.get_num_success_message()
        message = f"{num_success}"
        status = self.get_status()

        if status == StatusesEnum.NOT_STARTED:
            message += " - Not Started"
        elif status == StatusesEnum.PENDING:
            message += " - Queued"
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
            return StatusesEnum.NOT_STARTED

        if self.get_num_not_started() == len(self.work_containers):
            return StatusesEnum.NOT_STARTED

        if len(self.work_containers) == self.get_num_pending()\
                or len(self.work_containers) == (self.get_num_pending() + self.get_num_not_started()):
            return StatusesEnum.PENDING

        if self.get_num_failed() > 0:
            return StatusesEnum.FAILURE

        if (self.get_num_in_progress() + self.get_num_pending()) > 0:
            return StatusesEnum.IN_PROGRESS

        return StatusesEnum.SUCCESS

    def get_status_messages(self):
        return [
            container.get_status_message() for container in self.work_containers if not container.is_hidden
        ]

    def get_start_time(self, with_refresh=False):
        if len(self.work_containers) == self.get_num_not_started():
            return None
        else:
            start_times = [
                WorkContainerGroup.get_start_time(self=container, with_refresh=with_refresh)
                if isinstance(container, WorkContainerGroup) else
                container.get_start_time(with_refresh=with_refresh)
                for container in self.work_containers
            ]

            # filter Nones
            start_times = [start_time for start_time in start_times if start_time is not None]

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

        return total_progress / max(len(self.work_containers), 1)

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

    def get_num_not_started(self):
        return self.get_num_by_status(StatusesEnum.NOT_STARTED)

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


