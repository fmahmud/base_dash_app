import abc
import uuid

from redis import StrictRedis


class AbstractRedisDto(abc.ABC):
    def __init__(
        self,
        *args,
        redis_client: StrictRedis = None,
        ignore_nones: bool = True,
        **kwargs
    ):
        self.redis_client: StrictRedis = redis_client
        self.uuid: str = uuid.uuid4().hex
        self.read_only: bool = False
        self.ignore_nones: bool = ignore_nones

    @classmethod
    def from_redis(cls, *args, redis_client: StrictRedis, uuid: str, **kwargs):
        if not redis_client:
            raise ValueError("Redis client is None")

        if not uuid or uuid == "":
            raise ValueError("UUID is required")

        exists_in_redis = redis_client.exists(uuid)
        if exists_in_redis == 0:
            return None

        return cls(*args, **kwargs).use_redis(redis_client, uuid).hydrate_from_redis()

    def hydrate_from_redis(self):
        previous_read_only = self.read_only
        self.set_read_only()
        self.fetch_all_from_redis()
        self.set_read_only(previous_read_only)
        return self

    def set_read_only(self, read_only: bool = True):
        self.read_only = read_only

    def set_value_in_redis(self, key: str, value):
        if self.redis_client is None:
            return

        if self.read_only:
            return

        if value is None:
            if self.ignore_nones:
                return
            value = ""

        self.redis_client.hset(self.uuid, key, value)

    def get_value_from_redis(self, key: str) -> str:
        if self.redis_client is None:
            raise ValueError("Redis client is not set")

        return self.redis_client.hget(self.uuid, key)

    @abc.abstractmethod
    def to_dict(self) -> dict:
        pass

    @abc.abstractmethod
    def from_dict(self, data: dict):
        pass

    def use_redis(self, redis_client: StrictRedis, uuid: str):
        self.redis_client = redis_client
        self.uuid = uuid
        return self

    def push_to_redis(self):
        if self.redis_client is None:
            raise ValueError("Redis client is not set")

        if self.read_only:
            raise ValueError("This object is read only")

        for k, v in self.to_dict().items():
            self.set_value_in_redis(k, v)

        self.redis_client.hset(self.uuid, "uuid", self.uuid)

    def fetch_all_from_redis(self):
        if self.redis_client is None:
            raise ValueError("Redis client is not set")

        data = self.redis_client.hgetall(self.uuid)

        if len(data) == 0:
            return None

        return self.from_dict(data)

    def destroy_in_redis(self, expire: int = 0):
        if self.redis_client is None:
            raise ValueError("Redis client is not set")

        if expire > 0:
            self.redis_client.expire(self.uuid, expire)
        else:
            self.redis_client.delete(self.uuid)

