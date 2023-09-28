from base_dash_app.application.celery_decleration import CelerySingleton
from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.base_service import BaseService
from base_dash_app.virtual_objects.async_vos.celery_task import CeleryTask


# todo: for chains .apply_async(link_error=error_handler.s())


class CeleryHandlerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def submit_celery_task(self, celery_task: CeleryTask, *args, **kwargs):
        celery_task.use_redis(self.redis_client, celery_task.uuid)
        celery_task.reset(destroy_in_redis=True)

        celery_singleton = CelerySingleton.get_instance()
        celery_singleton.get_celery().backend.ensure_chords_allowed()

        # todo: maybe think of pulling push_to_redis out as a separate step outside of signature
        if "prev_result_uuids" not in kwargs:
            kwargs["prev_result_uuids"] = []

        something = celery_task.signature(**kwargs).apply_async()
        self.logger.info(f"Submitted celery task {celery_task.name} with id {something}")
