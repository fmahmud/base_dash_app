from typing import Optional

from base_dash_app.enums.status_colors import StatusesEnum

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
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.completed: bool = False
        self.extras = {}

    def get_status(self):
        if self.prerequisites_status in passing_statuses:
            if self.execution_status in passing_statuses:
                return self.completion_criteria_status
            else:
                return self.execution_status
        else:
            return self.prerequisites_status
