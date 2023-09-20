import datetime
import json
import logging
from enum import Enum
from typing import Optional, TypeVar, Type

from redis import Redis, StrictRedis

from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.utils import date_utils
from base_dash_app.virtual_objects.abstract_redis_dto import AbstractRedisDto
from base_dash_app.virtual_objects.interfaces.selectable import Selectable

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]

BASE_KEY = "VirtualJobProgressContainer"


class ContainerNotFoundError(Exception):
    pass


class VirtualJobProgressContainer(AbstractRedisDto):
    """
    Instances of this class will be created to help communicate between the executor thread and the
    server thread. It will contain the progress of the job as it runs.
    """

    @staticmethod
    def get_from_redis_by_uuid(redis_client: StrictRedis, uuid: str) -> Optional["VirtualJobProgressContainer"]:
        if not redis_client:
            raise ValueError("Redis client is None")

        if not uuid or uuid == "":
            raise ValueError("UUID is required")

        exists_in_redis = redis_client.exists(uuid)
        if exists_in_redis == 0:
            raise ContainerNotFoundError(f"Container with uuid {uuid} not found in redis")

        container = VirtualJobProgressContainer(job_instance_id=-2, job_definition_id=-2)
        container.use_redis(redis_client, uuid).hydrate_from_redis()
        return container

    def to_dict(self) -> dict:
        return {
            "job_instance_id": str(self.job_instance_id),
            "job_definition_id": str(self.job_definition_id),
            "execution_status": self.execution_status.value.name,
            "prerequisites_status": self.prerequisites_status.value.name,
            "completion_status": self.completion_criteria_status.value.name,
            "progress": self.progress if self.progress is not "" else 0.0,
            "logs": json.dumps(self.logs or []),
            "completed": "True" if self.completed else "False",
            "start_time": datetime.datetime.strftime(
                self.start_time, date_utils.STANDARD_DATETIME_FORMAT
            ) if self.start_time else "",
        }

    def from_dict(self, data: dict):
        self.job_instance_id = int(data.get("job_instance_id", -1))
        self.job_definition_id = int(data.get("job_definition_id", -1))
        self.execution_status = StatusesEnum.get_by_name(data.get("execution_status", StatusesEnum.PENDING.value.name))
        self.prerequisites_status = StatusesEnum.get_by_name(data.get("prerequisites_status", StatusesEnum.PENDING.value.name))
        self.completion_criteria_status = StatusesEnum.get_by_name(data.get("completion_status", StatusesEnum.PENDING.value.name))
        self.progress = float(data.get("progress", 0.0))
        self.uuid = f"{BASE_KEY}_{self.job_instance_id}"
        self.logs = json.loads(data.get("logs", "[]"))
        self.completed = data.get("completed", "False") == "True"
        self.start_time = data.get("start_time", "")
        if self.start_time == "":
            self.start_time = None
        else:
            self.start_time = datetime.datetime.strptime(
                self.start_time, date_utils.STANDARD_DATETIME_FORMAT
            )
        return self

    def __init__(self, job_instance_id: int, job_definition_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = f"{BASE_KEY}_{job_instance_id}"
        self.job_instance_id: int = job_instance_id
        self.job_definition_id: int = job_definition_id
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.prerequisites_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.completion_criteria_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = 0
        self.start_time = None
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.completed: bool = False
        self.extras = {}
        self.logs = []
        self.log_level: LogLevel = LogLevelsEnum.INFO.value
        self.logger = logging.getLogger(f"job_instance_{self.job_instance_id}")
        self.selectable: Optional[Selectable] = None
        self.last_status_updated_at: Optional[datetime.datetime] = None
        self.redis_client: Optional[Redis] = None
        self.celery_task_id: Optional[str] = None
        self.logs_tail_id = f"{self.uuid}_logs_tail"

    def __repr__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        if type(other) != type(self):
            return False

        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.job_instance_id)

    def __str__(self):
        return f"JobProgressContainer(job_instance_id={self.job_instance_id}, " \
               f"job_definition_id={self.job_definition_id}, " \
               f"execution_status={self.execution_status}, " \
               f"prerequisites_status={self.prerequisites_status}, " \
               f"completion_criteria_status={self.completion_criteria_status}, " \
               f"result={self.result}, " \
               f"start_time={self.start_time}, " \
               f"end_time={self.end_time}, " \
               f"end_reason={self.end_reason}, " \
               f"progress={self.progress}, " \
               f"completed={self.completed}, " \
               f"extras={self.extras}, " \
               f"logs={self.logs}, " \
               f"selectable: {self.selectable})"

    def set_progress(self, progress):
        if not progress:
            print("Progress is none")
            return
        self.progress = progress
        self.last_status_updated_at = datetime.datetime.now()
        self.set_value_in_redis("progress", progress or 0.0)

    def set_pending(self):
        self.execution_status = StatusesEnum.PENDING
        self.prerequisites_status = StatusesEnum.PENDING
        self.completion_criteria_status = StatusesEnum.PENDING
        self.last_status_updated_at = datetime.datetime.now()

    def set_in_progress(self):
        self.execution_status = StatusesEnum.IN_PROGRESS
        self.prerequisites_status = StatusesEnum.IN_PROGRESS
        self.completion_criteria_status = StatusesEnum.IN_PROGRESS
        self.last_status_updated_at = datetime.datetime.now()

    def complete(self, result=None, status=StatusesEnum.SUCCESS, progress=100, status_message=None, stacktrace=None):
        self.execution_status = status
        self.prerequisites_status = status
        self.completion_criteria_status = status
        self.result = result
        self.progress = progress
        self.completed = True
        self.end_time = datetime.datetime.now()
        self.end_reason = status_message
        self.last_status_updated_at = datetime.datetime.now()
        if stacktrace:
            self.error_log(stacktrace)

    def get_status(self):
        if self.prerequisites_status in passing_statuses:
            if self.execution_status in passing_statuses:
                return self.completion_criteria_status
            else:
                return self.execution_status
        else:
            return self.prerequisites_status

    def is_in_progress(self):
        return self.get_status() in StatusesEnum.get_non_terminal_statuses()

    def get_duration(self):
        if self.start_time is None:
            return 0

        if self.end_time is None:
            return (datetime.datetime.now() - self.start_time).total_seconds()

        return (self.end_time - self.start_time).total_seconds()

    def info_log(self, message):
        self.logger.info(message)
        if self.log_level <= LogLevelsEnum.INFO.value:
            self.logs.append(f"[INFO]{message}")

        if self.redis_client is not None:
            self.redis_client.rpush(
                self.logs_tail_id,
                f"[INFO]{message}\n"
            )

    def error_log(self, message):
        self.logger.error(message)
        if self.log_level <= LogLevelsEnum.ERROR.value:
            self.logs.append(f"[ERROR]{message}")

        if self.redis_client is not None:
            self.redis_client.rpush(
                self.logs_tail_id,
                f"[ERROR]{message}\n"
            )

    def critical_log(self, message):
        self.logger.critical(message)
        if self.log_level <= LogLevelsEnum.CRITICAL.value:
            self.logs.append(f"[CRITICAL]{message}")

        if self.redis_client is not None:
            self.redis_client.rpush(
                self.logs_tail_id,
                f"[CRITICAL]{message}\n"
            )

    def debug_log(self, message):
        self.logger.debug(message)
        if self.log_level <= LogLevelsEnum.DEBUG.value:
            self.logs.append(f"[DEBUG]{message}")

        if self.redis_client is not None:
            self.redis_client.rpush(
                self.logs_tail_id,
                f"[DEBUG]{message}\n"
            )

    def warn_log(self, message):
        self.logger.warning(message)
        if self.log_level <= LogLevelsEnum.WARNING.value:
            self.logs.append(f"[WARN]{message}")

        if self.redis_client is not None:
            self.redis_client.rpush(
                self.logs_tail_id,
                f"[WARN]{message}\n"
            )
