import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from base_dash_app.enums.log_levels import LogLevel, LogLevelsEnum
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService


class AsyncWorkProgressContainer:
    def __init__(self):
        self.execution_status: Optional[StatusesEnum] = StatusesEnum.PENDING
        self.result = 0
        self.start_time = None
        self.end_time = None
        self.end_reason = None
        self.progress: float = 0.0
        self.extras = {}
        self.logs = []
        self.log_level: LogLevel = LogLevelsEnum.INFO.value
        self.future = None

    def start(self):
        self.start_time = datetime.datetime.now()
        self.execution_status = StatusesEnum.IN_PROGRESS
        self.progress = 0

    def complete(self, result=1, status=StatusesEnum.SUCCESS, progress=100):
        self.end_time = datetime.datetime.now()
        self.execution_status = status
        self.result = result
        self.progress = progress


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
