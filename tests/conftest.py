"""The conf file which contains the fixtures used."""
import asyncio
import random
import string
from collections.abc import Hashable
from time import sleep
from typing import Callable

import pytest
from redis import Redis

from dspinlock import HashDSpinlock
from dspinlock.utils import create_redis_conn

_STR_ALPHABET = string.ascii_lowercase + string.digits
"""The alphabet for our sampling strategy"""


@pytest.fixture
def redis_session() -> Redis:
    """
    Returns the redis session

    Returns
    -------
    Redis
        The redis session to use.
    """
    return create_redis_conn()


@pytest.fixture
def hashable_string_factory(str_length: int = 20) -> Callable:
    """
    Generate an instance to use for the computation.

    Returns
    -------
    Callable
        The object factory that returns objects that adhere to `Hashable`.
    """

    def _make_hashable_strings() -> Hashable:
        return "".join(random.sample(_STR_ALPHABET, str_length))

    return _make_hashable_strings


async def query_task(
    task_id: int,
    obj: str,
    fail_if_key_exists: bool = False,
    cached_if_computed: bool = False,
    time_to_wait: float = 0,
):
    """
    Query a task that executes through atomic query.

    Parameters
    ----------
    task_id: int
        The task id.
    obj: Hashable
        The hashable object instance.
    fail_if_key_exists: bool = False
        Indicates if we fail should the key already exists - i.e. in cases when we want to block computation for
        a certain period.
    cached_if_computed: bool = False
        Indicates if the result is computed can be returned from a cache. Thus, we do not have to wait for its
        computation; hence, we can return immediately _without_ practically getting the lock.
    time_to_wait: float = 0
        The base amount of time to wait for tasks, default is 0 secs.
    """
    with HashDSpinlock(obj, fail_if_key_exists=fail_if_key_exists, cached_if_computed=cached_if_computed):
        print(f"executed task_id {task_id}")
        #
        if time_to_wait > 0:
            sleep(time_to_wait)

        # sleep a bit for even tasks
        if task_id % 2 == 0:
            await asyncio.sleep(0.5)


@pytest.fixture
async def spawner_factory() -> Callable:
    """The task spawner factory fixture."""

    async def _spawner(
        obj_to_use: str, fail_if_key_exists: bool = False, cached_if_computed: bool = False, time_to_wait: float = 0
    ):
        """The spawner for the tasks"""
        return await asyncio.gather(
            query_task(1, obj_to_use, fail_if_key_exists, cached_if_computed, time_to_wait),
            query_task(2, obj_to_use, fail_if_key_exists, cached_if_computed, time_to_wait),
        )

    return _spawner
