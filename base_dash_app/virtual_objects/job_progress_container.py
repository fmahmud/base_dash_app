import datetime
import logging
from enum import Enum
from typing import Optional, TypeVar, Type

from redis import Redis

from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.selectable import Selectable

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]

BASE_KEY = "VirtualJobProgressContainer"


class ContainerNotFoundError(Exception):
    pass


class VJPCRedisKeys(Enum):
    PROGRESS = lambda instance_id: f"{BASE_KEY}_{instance_id}.progress"
    EXECUTION_STATUS = lambda instance_id: f"{BASE_KEY}_{instance_id}.execution_status"
    PREREQUISITES_STATUS = lambda instance_id: f"{BASE_KEY}_{instance_id}.prerequisites_status"
    COMPLETION_CRITERIA_STATUS = lambda instance_id: f"{BASE_KEY}_{instance_id}.completion_criteria_status"
    LAST_STATUS_UPDATED_AT = lambda instance_id: f"{BASE_KEY}_{instance_id}.last_status_updated_at"
    LOGS = lambda instance_id: f"{BASE_KEY}_{instance_id}.logs"

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)


class VirtualJobProgressContainer:
    """
    Instances of this class will be created to help communicate between the executor thread and the
    server thread. It will contain the progress of the job as it runs.
    """

    def __init__(self, job_instance_id: int, job_definition_id: int):
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

    def __repr__(self):
        return str({
            "job_instance_id": self.job_instance_id,
            "job_definition_id": self.job_definition_id,
            "execution_status": self.execution_status.value.name,
            "prerequisites_status": self.prerequisites_status.value.name,
            "completion_criteria_status": self.completion_criteria_status.value.name,
            "progress": self.progress,
        })

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove the redis_client and logger before serializing
        del state['redis_client']
        del state['logger']
        del state["execution_status"]
        del state["prerequisites_status"]
        del state["completion_criteria_status"]
        del state["last_status_updated_at"]
        del state["selectable"]  # todo: how to recover this?
        state["log_level"] = state["log_level"].id
        return state

    def __setstate__(self, state):
        state["log_level"] = LogLevelsEnum.get_by_id(state["log_level"])
        # Restore the instance's attributes
        self.__dict__.update(state)
        # Reinitialize redis_client and logger after deserializing
        self.redis_client = None
        self.logger = logging.getLogger(f"job_instance_{self.job_instance_id}")
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.prerequisites_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.completion_criteria_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.last_status_updated_at: Optional[datetime.datetime] = None
        self.selectable = None  # todo: how to recover this? do we even need this?

    def use_redis(self, redis_client: Redis):
        self.redis_client = redis_client

    def fetch_latest_from_redis(self):
        if self.redis_client is None:
            self.logger.warning(f"Redis client not set for job_instance_id={self.job_instance_id}")
            return

        bin_prog_val = self.redis_client.get(VJPCRedisKeys.PROGRESS(self.job_instance_id))
        bin_exec_val = self.redis_client.get(VJPCRedisKeys.EXECUTION_STATUS(self.job_instance_id))
        bin_pre_val = self.redis_client.get(VJPCRedisKeys.PREREQUISITES_STATUS(self.job_instance_id))
        bin_comp_val = self.redis_client.get(VJPCRedisKeys.COMPLETION_CRITERIA_STATUS(self.job_instance_id))
        bin_last_status_updated_at = self.redis_client.get(VJPCRedisKeys.LAST_STATUS_UPDATED_AT(self.job_instance_id))

        if None not in [
            bin_prog_val, bin_exec_val, bin_pre_val, bin_comp_val, bin_last_status_updated_at
        ]:
            self.logger.debug(f"Found container for job_instance_id={self.job_instance_id}")
            # something to show?
            self.progress = float((bin_prog_val or b"0.0").decode("utf-8"))
            self.execution_status = StatusesEnum.get_by_name((bin_exec_val or b"PENDING").decode('utf-8'))
            self.prerequisites_status = StatusesEnum.get_by_name((bin_pre_val or b"PENDING").decode('utf-8'))
            self.completion_criteria_status = StatusesEnum.get_by_name((bin_comp_val or b"PENDING").decode('utf-8'))
            self.last_status_updated_at = datetime.datetime.strptime(
                (bin_last_status_updated_at or b"").decode("utf-8"),"%Y-%m-%d %H:%M:%S.%f"
            ) if bin_last_status_updated_at is not None else None
        else:
            self.logger.debug(f"Could not find container for job_instance_id={self.job_instance_id}")
            raise ContainerNotFoundError(f"Could not find container for job_instance_id={self.job_instance_id}")

        # todo: parse logs?
        self.logs = (self.redis_client.get(VJPCRedisKeys.LOGS(self.job_instance_id)) or b"").decode("utf-8").split("\n")

    def push_changes_to_redis(self):
        if self.redis_client is None:
            return

        self.redis_client.set(
            VJPCRedisKeys.PROGRESS(self.job_instance_id),
            self.progress
        )
        self.redis_client.set(
            VJPCRedisKeys.EXECUTION_STATUS(self.job_instance_id),
            self.execution_status.value.name
        )
        self.redis_client.set(
            VJPCRedisKeys.PREREQUISITES_STATUS(self.job_instance_id),
            self.prerequisites_status.value.name
        )
        self.redis_client.set(
            VJPCRedisKeys.COMPLETION_CRITERIA_STATUS(self.job_instance_id),
            self.completion_criteria_status.value.name
        )
        self.redis_client.set(
            VJPCRedisKeys.LAST_STATUS_UPDATED_AT(self.job_instance_id),
            str(self.last_status_updated_at)
        )

    def clear_redis(self):
        if self.redis_client is None:
            return

        self.logger.info(f"Clearing redis for job_instance_id={self.job_instance_id}")
        self.redis_client.delete(VJPCRedisKeys.PROGRESS(self.job_instance_id))
        self.redis_client.delete(VJPCRedisKeys.EXECUTION_STATUS(self.job_instance_id))
        self.redis_client.delete(VJPCRedisKeys.PREREQUISITES_STATUS(self.job_instance_id))
        self.redis_client.delete(VJPCRedisKeys.COMPLETION_CRITERIA_STATUS(self.job_instance_id))
        self.redis_client.delete(VJPCRedisKeys.LAST_STATUS_UPDATED_AT(self.job_instance_id))
        self.redis_client.delete(VJPCRedisKeys.LOGS(self.job_instance_id))

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
            self.redis_client.append(
                VJPCRedisKeys.LOGS(self.job_instance_id),
                f"[INFO]{message}\n"
            )

    def error_log(self, message):
        self.logger.error(message)
        if self.log_level <= LogLevelsEnum.ERROR.value:
            self.logs.append(f"[ERROR]{message}")

        if self.redis_client is not None:
            self.redis_client.append(
                VJPCRedisKeys.LOGS(self.job_instance_id),
                f"[ERROR]{message}\n"
            )

    def critical_log(self, message):
        self.logger.critical(message)
        if self.log_level <= LogLevelsEnum.CRITICAL.value:
            self.logs.append(f"[CRITICAL]{message}")

        if self.redis_client is not None:
            self.redis_client.append(
                VJPCRedisKeys.LOGS(self.job_instance_id),
                f"[CRITICAL]{message}\n"
            )

    def debug_log(self, message):
        self.logger.debug(message)
        if self.log_level <= LogLevelsEnum.DEBUG.value:
            self.logs.append(f"[DEBUG]{message}")

        if self.redis_client is not None:
            self.redis_client.append(
                VJPCRedisKeys.LOGS(self.job_instance_id),
                f"[DEBUG]{message}\n"
            )

    def warn_log(self, message):
        self.logger.warning(message)
        if self.log_level <= LogLevelsEnum.WARNING.value:
            self.logs.append(f"[WARN]{message}")

        if self.redis_client is not None:
            self.redis_client.append(
                VJPCRedisKeys.LOGS(self.job_instance_id),
                f"[WARN]{message}\n"
            )
