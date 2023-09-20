from typing import Dict, Any, List, Optional

from celery import Task, chain, group, chord

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.virtual_objects.async_vos import celery_helpers
from base_dash_app.virtual_objects.async_vos.work_containers import WorkContainer, WorkContainerGroup


class CeleryTask(WorkContainer):

    def __init__(
            self,
            name: str = None, color: str = None, icon: str = None, is_hidden: bool = False,
            work_func=None, func_kwargs: Dict[str, Any] = None,
            **kwargs
    ):
        """
        :param name: the name of the task
        :param color: the color of the task when displaying it in the UI
        :param icon: the icon of the task when displaying it in the UI
        :param is_hidden: whether to hide it in the UI
        :param work_func: the celery task to execute
        :param func_kwargs: the kwargs to pass to the celery task
        :param kwargs: the kwargs to pass to the WorkContainer
        """
        super().__init__(
            name=name,
            color=color,
            icon=icon,
            is_hidden=is_hidden,
            **kwargs
        )  # redis_client sent to AbstractRedisDto
        self.work_func: Optional[Task] = None
        self.func_kwargs: Dict[str, Any] = func_kwargs or {}

        self.set_work_func(work_func)

    def set_work_func(self, work_func):
        self.work_func = work_func if work_func else None
        return self

    def set_func_kwargs(self, func_kwargs: Dict[str, Any]):
        self.func_kwargs = func_kwargs
        return self

    def set_func_kwargs_item(self, key: str, value: Any):
        self.func_kwargs[key] = value
        return self

    def signature(self, *args, prev_result_uuids: List[str], **kwargs):
        self.push_to_redis()
        return self.work_func.s(
            *args,
            prog_container_uuid=self.uuid,
            prev_result_uuids=prev_result_uuids,
            **self.func_kwargs,
            **kwargs
        )


class CeleryOrderedTaskGroup(WorkContainerGroup, CeleryTask):
    def __init__(
            self,
            name: str = None, color: str = None, icon: str = None, is_hidden: bool = False,
            tasks: List[CeleryTask] = None,
            chain_results: bool = True,
            **kwargs
    ):
        super().__init__(
            containers=tasks,
            name=name,
            color=color,
            icon=icon,
            is_hidden=is_hidden,
            **kwargs
        )
        self.tasks: List[CeleryTask] = tasks or []
        self.chain_results: bool = chain_results

    def add_task(self, task: CeleryTask):
        self.tasks.append(task)
        super().add_container(task)

    def signature(self, *args, prev_result_uuids: List[str], **kwargs):
        prev_result = prev_result_uuids
        task_chain = []
        for i, task in enumerate(self.tasks):
            task_chain.append(task.signature(*args, prev_result_uuids=prev_result, **kwargs))
            if self.chain_results:
                prev_result = [task.uuid]
            else:
                prev_result = []

        self.push_to_redis()
        return chain(*task_chain)

    def get_result(self, *args, **kwargs):
        if not self.work_containers:
            return None

        if self.get_status() in StatusesEnum.get_non_terminal_statuses():
            return None

        if len(self.work_containers) == 0:
            return None

        last_task = self.work_containers[-1]
        if isinstance(last_task, CeleryOrderedTaskGroup):
            result = CeleryOrderedTaskGroup.get_result(last_task)
        elif isinstance(last_task, CeleryUnorderedTaskGroup):
            result = CeleryUnorderedTaskGroup.get_result(last_task)
        else:
            print(f"{self.name}|{self.uuid}: {last_task.to_dict()}")
            result = last_task.get_result()
            if result is None:
                print(f"{self.name}|{self.uuid}: result is None")
                result = []

        print(f"{self.name}: Group result size: {len(result)}")
        return result


class CeleryUnorderedTaskGroup(WorkContainerGroup, CeleryTask):
    def __init__(
            self,
            name: str, color: str = None, icon: str = None, is_hidden: bool = False,
            tasks: List[CeleryTask] = None,
            reducer_task: Task = None,
            require_all_success: bool = True,
            **kwargs
    ):
        super().__init__(
            containers=tasks,
            name=name,
            color=color,
            icon=icon,
            is_hidden=is_hidden,
            **kwargs
        )
        self.tasks: List[CeleryTask] = tasks or []
        self.reducer_task = (reducer_task or celery_helpers.store_uuids).s(
            target_uuid=self.uuid,
            hash_key="result",
            prev_result_uuids=[]
        )
        self.require_all_success: bool = require_all_success

    def get_result(self, *args, **kwargs):
        if not self.work_containers:
            return None

        if self.get_status() in StatusesEnum.get_non_terminal_statuses():
            return None

        if len(self.work_containers) == 0:
            return None

        last_task = self.work_containers[-1]
        if isinstance(last_task, CeleryOrderedTaskGroup):
            result = CeleryOrderedTaskGroup.get_result(last_task)
        elif isinstance(last_task, CeleryUnorderedTaskGroup):
            result = CeleryUnorderedTaskGroup.get_result(last_task)
        else:
            result = last_task.get_result() or []

        return result

    def add_task(self, task: CeleryTask):
        self.tasks.append(task)

    def signature(self, *args, prev_result_uuids: List[str], **kwargs):
        if self.require_all_success:
            task_list = [
                chain(
                    celery_helpers.abort_on_failure.s(target_uuid=self.uuid),
                    task.signature(*args, prev_result_uuids=prev_result_uuids, **kwargs)
                )
                for task in self.tasks
            ]
        else:
            task_list = [
                task.signature(*args, prev_result_uuids=prev_result_uuids, **kwargs)
                for task in self.tasks
            ]

        self.push_to_redis()
        return chord(
            header=task_list,
            body=self.reducer_task
        ).on_error(
            celery_helpers.handle_chord_error.s(
                target_uuid=self.uuid
            )
        )

