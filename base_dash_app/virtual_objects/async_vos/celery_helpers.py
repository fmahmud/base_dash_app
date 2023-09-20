import json
from typing import List

from celery import shared_task, Task, states
from redis import StrictRedis

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.utils import redis_utils
from base_dash_app.virtual_objects.async_vos.work_containers import WorkContainerGroup


@shared_task
def flatten_redis_lists(*args, prev_result_uuids: List[str], target_uuid: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    redis_utils.flatten_redist_list(target_uuid, prev_result_uuids, redis_client)


@shared_task
def store_uuids(*args, prev_result_uuids: List[str], target_uuid: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    for uuid in prev_result_uuids:
        redis_client.rpush(target_uuid, uuid)


@shared_task
def serialize_uuids(*args, prev_result_uuids: List[str], target_uuid: str, hash_key: str = None, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    if hash_key is None:
        redis_client.set(target_uuid, json.dumps(prev_result_uuids))
    else:
        redis_client.hset(target_uuid, hash_key, json.dumps(prev_result_uuids))


@shared_task
def serialize_flattened_result_lists(*args, prev_result_uuids: List[str], target_uuid: str, hash_key: str = None, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    results = []
    for uuid in prev_result_uuids:
        results.append(redis_client.lrange(uuid, 0, -1))

    if hash_key is None:
        redis_client.set(target_uuid, json.dumps(results))
    else:
        redis_client.hset(target_uuid, hash_key, json.dumps(results))


@shared_task(bind=True)
def abort_on_failure(task: Task, *args, target_uuid: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    key_type = redis_client.type(target_uuid)
    if key_type == "hash":
        value = redis_client.hgetall(target_uuid)
        if "error" in value and value["error"]:
            task.update_state(
                state=states.FAILURE
            )


@shared_task
def handle_chord_error(*args, target_uuid: str, request, exc, traceback, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    print(f"Chord error for {target_uuid}")
    print(f"Request: {request}")
    print(f"Exception: {exc}")
    print(f"Traceback: {traceback}")

    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    key_type = redis_client.type(target_uuid)
    if key_type == "hash":
        value = redis_client.hgetall(target_uuid)
        if "type" in value:
            if value["type"] == "WorkContainerGroup":
                # hydrate WorkContainerGroup by uuid
                work_container_group = (
                    WorkContainerGroup()
                        .use_redis(redis_client, target_uuid)
                        .hydrate_from_redis()
                )

                # get uuid of task that failed
                failed_uuid = request.kwargs["prog_container_uuid"]
                print(f"WorkContainerGroup {target_uuid} contains failed task: {failed_uuid}")
                failed_task = work_container_group.get_container_by_uuid(failed_uuid)
                failed_task.set_stacktrace(traceback)
                failed_task.set_status(StatusesEnum.FAILED.value.name)
                failed_task.set_status_message("Task failed: " + str(exc))
                failed_task.set_read_only(False)
                failed_task.push_to_redis()
                failed_task.set_read_only()

                work_container_group.set_read_only(False)
                work_container_group.push_to_redis()

            elif value["type"] == "WorkContainer":
                print(f"WorkContainer {target_uuid} failed: {exc}")
            else:
                print(f"Unknown type {value['type']} for {target_uuid}")



