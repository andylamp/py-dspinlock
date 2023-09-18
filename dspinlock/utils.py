"""Module that contains useful utilities."""
from typing import Literal

import redis


def create_redis_conn(
    redis_host: str,
    rdb: int,
    port: int = 6379,
    ssl: bool = False,
    decode_responses: Literal[True, False] = True,
) -> redis.Redis:
    """
    Function that helps connect to the Redis database.

    Parameters
    ----------
    redis_host: str
        The Redis host that we will connect to.
    rdb: int
        The Redis database to use.
    port: int
        The Redis port - default 6379.
    ssl: bool
        If we are using SSL with Redis or not - default False.
    decode_responses: Literal[True, False]
        Checks if we decode responses
    Returns
    -------
    redis.Redis
        An initialised redis instance, which is also stored as a class variable.
    """

    return redis.Redis(
        host=redis_host, db=rdb, port=port, ssl=ssl, socket_connect_timeout=2, decode_responses=decode_responses
    )
