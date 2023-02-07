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
        self.completed: bool = False
        self.extras = {}
        self.logs = []
        self.log_level: LogLevel = LogLevelsEnum.INFO.value


class AsyncHandlerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.threadpool_executor = ThreadPoolExecutor(max_workers=10)

    def do_work(self, func, done_callback=None, *args, **kwargs):

        async_container: AsyncWorkProgressContainer = AsyncWorkProgressContainer()
        kwargs['async_container'] = async_container

        if done_callback is None:
            self.threadpool_executor.submit(func, *args, **kwargs)
        else:
            self.threadpool_executor.submit(func, *args, **kwargs).add_done_callback(done_callback)

        return async_container