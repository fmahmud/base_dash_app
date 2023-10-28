from celery.result import AsyncResult
from redis import StrictRedis

from base_dash_app.application.celery_decleration import CelerySingleton
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService
from base_dash_app.virtual_objects.async_vos.celery_task import CeleryTask, CeleryOrderedTaskGroup, \
    CeleryUnorderedTaskGroup
from base_dash_app.virtual_objects.async_vos.work_containers import WorkContainerGroup, WorkContainer


# todo: for chains .apply_async(link_error=error_handler.s())


class CeleryHandlerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset_celery_task(self, celery_task: CeleryTask, *args, **kwargs):
        celery_task.use_redis(self.redis_client, celery_task.uuid)
        if isinstance(celery_task, CeleryOrderedTaskGroup):
            for task in celery_task.tasks:
                self.reset_celery_task(task)
        elif isinstance(celery_task, CeleryUnorderedTaskGroup):
            for task in celery_task.tasks:
                self.reset_celery_task(task)
        else:
            celery_task.reset(destroy_in_redis=True)

    def submit_celery_task(self, celery_task: CeleryTask, *args, **kwargs):
        redis_client: StrictRedis = self.redis_client
        if not redis_client.ping():
            self.logger.error("Redis client is not connected")
            raise ValueError("Redis client is not connected")

        self.reset_celery_task(celery_task)

        celery_singleton = CelerySingleton.get_instance()
        celery_singleton.get_celery().backend.ensure_chords_allowed()

        # todo: maybe think of pulling push_to_redis out as a separate step outside of signature
        if "prev_result_uuids" not in kwargs:
            kwargs["prev_result_uuids"] = []

        async_result: AsyncResult = celery_task.signature(**kwargs).apply_async(countdown=2)

        if async_result is None:
            self.logger.error(f"async_result is None for {celery_task.name}")
            raise Exception(f"async_result is None for {celery_task.name}")

        self.logger.info(f"Submitted celery task {celery_task.name} with task_id {async_result.task_id}")
        celery_task.celery_task_id = async_result.task_id
        celery_task.set_value_in_redis("task_id", celery_task.celery_task_id)

    def revoke(self, celery_task: CeleryTask, *args, **kwargs):
        self.logger.info(f"revoking celery task {celery_task.name}")
        celery_task.set_read_only(False)

        if isinstance(celery_task, CeleryOrderedTaskGroup):
            celery_task_as_group: CeleryOrderedTaskGroup = celery_task
            for task in celery_task_as_group.tasks:
                self.revoke(task)

            WorkContainerGroup.interrupt(celery_task_as_group, push_to_redis=True)
        elif isinstance(celery_task, CeleryUnorderedTaskGroup):
            celery_task_as_group: CeleryUnorderedTaskGroup = celery_task
            for task in celery_task_as_group.tasks:
                self.revoke(task)

            WorkContainerGroup.interrupt(celery_task_as_group, push_to_redis=True)
        else:
            if celery_task.celery_task_id is None:
                self.logger.error(f"Celery task {celery_task.name} has no celery task id")
                return

            self.logger.info(f"Revoking celery task {celery_task.name} with id {celery_task.celery_task_id}")

            async_result: AsyncResult = AsyncResult(
                celery_task.celery_task_id, app=CelerySingleton.get_instance().get_celery()
            )

            async_result.revoke(terminate=True)
            WorkContainer.interrupt(celery_task, push_to_redis=True)

        # convert this to use the id instead of the actual task - the task is not serializable
        celery_task.complete(
            # result="Stopped by User",
            status=StatusesEnum.FAILURE,
            status_message="Stopped by User",
        )

