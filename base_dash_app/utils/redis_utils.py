from typing import List

from redis import StrictRedis


def flatten_redist_list(destination_key: str, source_keys: List[str], redis_client: StrictRedis):
    for source_key in source_keys:
        redis_client.rpush(destination_key, redis_client.get(source_key))