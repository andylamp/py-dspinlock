"""Module that contains useful utilities."""
from dataclasses import dataclass
from typing import Literal

import redis


@dataclass
class RedisParameters:
    """The redis connection parameters."""

    redis_host: str = "localhost"
    """The Redis host that we will connect to, the default is `localhost`."""
    rdb: int = 0
    """The Redis database to use, the default is `0`."""
    port: int = 6379
    """The Redis port - the default is `6379`."""
    ssl: bool = False
    """If we are using SSL with Redis or not - the default is `False`."""
    socket_connect_timeout: float = 2
    """The socket connection timeout, in seconds."""
    decode_responses: bool = True
    """Flag if we are decoding `redis` engine responses, the default is `False`."""


def create_redis_conn(params: RedisParameters | None = None) -> redis.Redis:
    """
    Function that helps connect to the Redis database.

    Parameters
    ----------
    params: RedisParameters
        The redis parameters to use.

    Returns
    -------
    redis.Redis
        An initialised redis instance, which is also stored as a class variable.
    """

    # if the parameters are `None` then create one with the default values...
    params = RedisParameters() if params is None else params

    # this is a hack to satisfy mypy when used with a dataclass to pass literals
    # noinspection PyTypeChecker
    decode_resp: Literal[True, False] = params.decode_responses

    # try to create the redis connection.
    return redis.Redis(
        host=params.redis_host,
        db=params.rdb,
        port=params.port,
        ssl=params.ssl,
        socket_connect_timeout=params.socket_connect_timeout,
        decode_responses=decode_resp,
    )
