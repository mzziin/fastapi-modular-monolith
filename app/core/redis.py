from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from app.core.config import settings


def create_redis_client() -> Redis:
    return Redis.from_url(
        settings.redis_url.get_secret_value(),
        socket_connect_timeout=1,
        socket_timeout=1,
        # An attempt may already have been counted if the reply timed out.
        retry=Retry(NoBackoff(), 0),
    )
