"""Connections for Redis."""
import logging
import traceback
import contextlib
from typing import Iterator

from redis import Redis, RedisError, ConnectionError as RedisConnectionError

@contextlib.contextmanager
def connection(redis_uri) -> Iterator[Redis]:
    """Connection to redis"""
    rconn = Redis.from_url(redis_uri, decode_responses=True)
    try:
        if not rconn.ping():
            raise RedisConnectionError("Could not connect to Redis.")
        yield rconn
    except RedisError as _rerr:
        logging.debug(traceback.format_exc())
        raise
    finally:
        rconn.close()
