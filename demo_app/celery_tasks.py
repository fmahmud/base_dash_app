import datetime
import json
import logging
import random
import time
from typing import List

from celery import shared_task
from redis import StrictRedis

from base_dash_app.enums.status_colors import StatusesEnum
from base_dash_app.services.async_handler_service import AsyncWorkProgressContainer
from base_dash_app.virtual_objects.async_vos.celery_task import CeleryTask
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


@shared_task
def gen_graph_data(*args, prog_container_uuid: str, prev_result_uuids: List[str], **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    prog_container = CeleryTask().use_redis(redis_client, prog_container_uuid).hydrate_from_redis()
    prog_container.set_status(StatusesEnum.IN_PROGRESS)

    logger = logging.getLogger(f"{prog_container.name} - {prog_container.uuid}")
    logger.info("Starting gen work func")
    time.sleep(random.randint(1, 2))
    prog_container.set_progress(25)
    prog_container.set_status_message("Generating Data...")
    time.sleep(1)
    prog_container.set_progress(50)
    time.sleep(random.randint(1, 2))
    prog_container.set_progress(75)
    # hydrate prev_result from uuid
    prev_result = []
    for uuid in prev_result_uuids:
        logger.info(f"Hydrating prev result from {uuid}")
        parsed_array = json.loads(redis_client.hget(uuid, "result") or "[]")
        logger.info(f"size of parsed array: {len(parsed_array)}")
        prev_result.extend(parsed_array)

    if prev_result:
        data = []
        for p in prev_result:
            p["value"] += random.randint(0, 100)

            data.append(TimeSeriesDataPoint().from_dict(p))
    else:
        data = [
            TimeSeriesDataPoint(
                date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                value=random.randint(0, 100)
            )
            for i in range(100)
        ]
    prog_container.complete(
        result=[d.to_dict() for d in data],
        status_message="Finished generating data"
    )
    logger.info("Finished work func")


@shared_task
def throw_exception_func(*args, prog_container_uuid: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    prog_container = CeleryTask().use_redis(redis_client, prog_container_uuid).hydrate_from_redis()
    prog_container.set_status(StatusesEnum.IN_PROGRESS)
    time.sleep(1)
    prog_container.complete(
        status=StatusesEnum.FAILURE,
        status_message="Demo Exception thrown",
        result="",
    )


@shared_task
def long_sleep_task(*args, prog_container_uuid: str, **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client: StrictRedis = RuntimeApplication.get_instance().redis_client
    prog_container = CeleryTask().use_redis(redis_client, prog_container_uuid).hydrate_from_redis()
    for i in range(20):
        prog_container.set_progress(i * 5)
        time.sleep(1)

    prog_container.complete(
        result="",
        status_message="Finished sleeping"
    )


