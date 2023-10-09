"""Test the atomic isolated functionality."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

import pytest
import redis

from dspinlock import FailIfKeyExistsIsEnabled, InvalidValueEncounteredDuringUnpacking, SpinlockTriesExceeded


def test_distributed_spinlock_mutex(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Tests that the distributed spinlock mutex works as a base case and both tasks execute correctly."""
    the_obj = hashable_string_factory()
    asyncio.run(spawner_factory(the_obj))
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # now delete it
    redis_session.delete(key)


def test_distributed_spinlock_mutex_fail_if_key_exists(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Tests that the spinlock mutex fails if key exists and the relevant flag is raised."""
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
    """Tests that the spinlock mutex returns immediately if the value is computed and can be cached."""
    the_obj = hashable_string_factory()
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # clear the messages from previous runs.
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        asyncio.run(spawner_factory(the_obj, cached_if_computed=True))
    # now delete it
    redis_session.delete(key)
    # ensure that the value only changed once.
    assert len([m for m in caplog.messages if "Changing the query mutex for key:" in m]) == 1


# noinspection DuplicatedCode
def test_spinlock_tries_exceeded(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Tests that the spinlock tries exceeded exception is thrown appropriately."""
    the_obj = hashable_string_factory()
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # set the value to be blocked now, so that the spinlock expires.
    redis_session.set(key, f"18b29dc6-208e-4456-a323-bc911e8ac18c,{datetime.now(tz=timezone.utc).isoformat()},0")

    with pytest.raises(SpinlockTriesExceeded):
        asyncio.run(spawner_factory(the_obj))

    redis_session.delete(key)


# noinspection DuplicatedCode
def test_spinlock_invalid_mutex_value_encountered(
    redis_session: redis.Redis, hashable_string_factory: Callable, spawner_factory: Callable
):
    """Tests the that the exception for invalid mutex value is thrown correctly."""
    the_obj = hashable_string_factory()
    # compose the key based on the object
    key = f"dspinlock,{hash(the_obj)}"
    # set the value to be blocked now, so that the spinlock expires.
    redis_session.set(key, f"18b29dc6-208e-4456-a323-bc911e8ac18c,{datetime.now(tz=timezone.utc).isoformat()},0,asdsa")

    with pytest.raises(InvalidValueEncounteredDuringUnpacking):
        asyncio.run(spawner_factory(the_obj))

    redis_session.delete(key)
