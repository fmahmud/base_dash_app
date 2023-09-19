import datetime
import logging
import random
import time
from typing import List

from celery import shared_task

from base_dash_app.services.async_handler_service import AsyncWorkProgressContainer
from base_dash_app.virtual_objects.timeseries.time_series_data_point import TimeSeriesDataPoint


@shared_task
def gen_graph_data(prog_container_uuid: str, prev_result_uuids: List[str], **kwargs):
    from base_dash_app.application.runtime_application import RuntimeApplication
    redis_client = RuntimeApplication.get_instance().redis_client
    prog_container = AsyncWorkProgressContainer()
    prog_container.use_redis(redis_client, prog_container_uuid)
    prog_container.fetch_latest_from_redis()

    logger = logging.getLogger("gen_graph_data")
    time.sleep(random.randint(1, 2))
    prog_container.set_progress(25)
    prog_container.set_status_message("Generating Data...")
    time.sleep(1)
    prog_container.set_progress(50)
    time.sleep(random.randint(1, 2))
    prog_container.set_progress(75)
    if prev_result:
        data = prev_result
        for d in data:
            d.value += random.randint(0, 100)
    else:
        data = [
            TimeSeriesDataPoint(
                date=datetime.datetime(year=2023, day=1, month=1) + datetime.timedelta(days=i),
                value=random.randint(0, 100)
            )
            for i in range(100)
        ]
    prog_container.complete(
        result=data,
        status_message="Finished generating data"
    )
    logger.info("Finished work func")