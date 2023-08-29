import datetime
import logging
from typing import Optional, Any, Tuple, FrozenSet

from base_dash_app.enums.log_levels import LogLevelsEnum, LogLevel
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.interfaces.selectable import Selectable

passing_statuses = [StatusesEnum.WARNING, StatusesEnum.SUCCESS]


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

    def error_log(self, message):
        self.logger.error(message)
        if self is not None \
                and self.log_level <= LogLevelsEnum.ERROR.value:
            self.logs.append(f"[ERROR]{message}")

    def critical_log(self, message):
        self.logger.critical(message)
        if self is not None \
                and self.log_level <= LogLevelsEnum.CRITICAL.value:
            self.logs.append(f"[CRITICAL]{message}")

    def debug_log(self, message):
        self.logger.debug(message)
        if self is not None \
                and self.log_level <= LogLevelsEnum.DEBUG.value:
            self.logs.append(f"[DEBUG]{message}")

    def warn_log(self, message):
        self.logger.warning(message)
        if self is not None \
                and self.log_level <= LogLevelsEnum.WARNING.value:
            self.logs.append(f"[WARN]{message}")