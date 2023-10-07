"""Test the atomic isolated functionality."""
import asyncio
from typing import Callable

import pytest
import redis

from dspinlock import FailIfKeyExistsIsEnabled


def test_distributed_spinlock_mutex(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Test the distributed asyncio spinlock mutex"""
    the_obj = hashable_string_factory()
    asyncio.run(spawner_factory(the_obj))
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # now delete it
    redis_session.delete(key)


def test_distributed_spinlock_mutex_fail_if_key_exists(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Test the distributed asyncio spinlock mutex"""
    the_obj = hashable_string_factory()

    # assert that it indeed fails when that happens
    with pytest.raises(FailIfKeyExistsIsEnabled):
        asyncio.run(spawner_factory(the_obj, fail_if_key_exists=True))
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # now delete it
    redis_session.delete(key)


def test_distributed_spinlock_mutex_return_immediately_if_computed(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable, caplog
):
    """Test the distributed asyncio spinlock mutex"""
    the_obj = hashable_string_factory()
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # clear the messages from previous runs.
    caplog.clear()
    asyncio.run(spawner_factory(the_obj, cached_if_computed=True))
    # now delete it
    redis_session.delete(key)
    # ensure that the value only changed once.
    assert len([m for m in caplog.messages if "Changing the query mutex for key:" in m]) == 1
