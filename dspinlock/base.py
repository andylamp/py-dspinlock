""""Module that contains query related utilities."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from math import ceil
from time import sleep
from typing import Any

import redis

from .consts import SL_LOG_TAG
from .exceptions import (
    AtomicQueryInvalidStateException,
    InvalidMutexReleaseEncountered,
    InvalidValueEncounteredDuringUnpacking,
    SpinlockTriesExceeded,
)

qlog = logging.getLogger(SL_LOG_TAG)
"""Get the logger."""


class QueryState(Enum):
    """The QueryState used to indicate its execution status."""

    BLOCKED = 0
    COMPUTED = 1


# pylint: disable=too-few-public-methods
@dataclass(order=True, frozen=True)
class UnpackedValue:
    """The unpacked value dataclass, used to store the parsed value from redis."""

    value: int
    """The value packed."""
    tag: str
    """The parsed tag."""
    req_id: str | None = None
    """The request id."""
    timestamp: datetime | None = None
    """The parsed timestamp."""


# pylint: disable=too-few-public-methods
class DSpinlockBase(ABC):
    """
    Class that ensures the query isolation in case of parallel requests.
    """

    max_spinlock_tries: int = 10
    """The spinlock max retries, by default 10 tries."""
    spinlock_sleep_thresh: float = 0.5
    """The spinlock sleep threshold, by default 0.5 seconds."""
    expire_at_timedelta: timedelta = timedelta(hours=1)
    """The expire at timedelta value, by default 1 hour."""
    tag_sep: str = ","
    """The tag separator."""
    value_sep: str = ","
    """The value separator."""
    max_block_time: timedelta = timedelta(hours=0.5)
    """The max block time allowed for a query mutex to be held, if not released it is forcefully unblocked."""

    # the redis session."""
    _sess: redis.Redis | None = None
    # the key prefix to use within redis
    _key_prefix: str = "dspinlock"

    def __init__(self, obj: Any, sess: redis.Redis):
        """
        The constructor which takes

        Parameters
        ----------
        obj: Any
            The object to create the lock for.
        sess: redis.Redis
            The session to redis.
        """
        self._sess = sess
        self._tag = self._set_tag(obj)
        self._sess = self._get_redis_sess()

    def __enter__(self):
        self._acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release()

    @abstractmethod
    def _set_tag(self, obj: Any):
        """
        Takes the object and produces a tag based on the desired attributes to take in account.

        Parameters
        ----------
        obj: Any
            The object instance.

        Returns
        -------

        """
        raise NotImplementedError

    def _unpack_value(self, value: str | None) -> UnpackedValue | None:
        """
        Unpacks the value from redis. The format of the stored value is the following,

            - req_id: the request id,
            - datetime ts: the datetime timestamp,
            - mutex value: the mutex current value

        Parameters
        ----------
        value: str | None
            The value as fetched from redis.

        Returns
        -------
        UnpackedValue | None
            The parsed `UnpackedValue` instance, `None` if the value is already `None`.
        """
        # initialise the unpacked value to `None`.
        unpacked_val = None

        # check if the value is None, which should happen when the key does not exist.
        if value is None:
            return unpacked_val

        tokens = value.split(self.value_sep)
        tok_num = len(tokens)

        if tok_num == 3:
            unpacked_val = UnpackedValue(
                value=int(tokens[2]),
                tag=f"{tokens[0]},{tokens[1]}",
                timestamp=datetime.fromisoformat(tokens[1]),
                req_id=tokens[0],
            )
        else:
            raise InvalidValueEncounteredDuringUnpacking(
                f"Unpacked a value with incorrect number of tokens, expected 3 or 4 got {tok_num}"
            )

        return unpacked_val

    def _tag_match(self, val: UnpackedValue) -> bool:
        """
        Function that checks if the unpacked values' tag matches the current instance one.

        Parameters
        ----------
        val: UnpackedValue
            The unpacked value instance.

        Returns
        -------
        bool
            Returns `True` if the value matches, `False` otherwise.
        """
        return val.tag == self._tag

    @staticmethod
    def _mutex_value_match(val: UnpackedValue, match_to: QueryState) -> bool:
        """
        Function that checks if the unpacked values' mutex value matches the target one.

        Parameters
        ----------
        val: UnpackedValue
            The unpacked value instance.
        match_to: QueryState
            The QueryState value to check against.

        Returns
        -------
        bool
            Returns `True` if the value matches, `False` otherwise.
        """
        return val.value == match_to.value

    def _get_expiry_unix_time(self) -> int:
        """
        Fetches the expiry unix time which is roughly 1 day after the current time.

        Returns
        -------
        int
            The timestamp to expire at.
        """
        return ceil((datetime.now(tz=timezone.utc) + self.expire_at_timedelta).timestamp())

    def _release(self):
        """Releases the distributed query mutex."""
        key = self.get_key()

        tries = 1
        res = None

        for _ in enumerate(range(self.max_spinlock_tries)):
            try:
                pipe = self._get_redis_sess().pipeline()
                pipe.watch(key)

                res = self._unpack_value(self._get_redis_sess().get(key))

                if res is None:
                    qlog.debug("Cannot release mutex for key: %s as the key was not existent...", self.get_key())
                    return

                if self._mutex_value_match(res, QueryState.BLOCKED):
                    if res.tag != self._tag:
                        raise InvalidMutexReleaseEncountered(
                            f"Encountered a blocked query mutex with tag: {res.tag} that is for "
                            "another query, this should not happen."
                        )
                    qlog.debug("Change the query mutex for key %s", self.get_key())
                    pipe.set(key, self._generate_payload(QueryState.COMPUTED), exat=self._get_expiry_unix_time())
                    pipe.execute()
                elif self._mutex_value_match(res, QueryState.COMPUTED):
                    qlog.debug("Query mutex required no release as its already computed with tag: %s.", res.tag)
                    break
                else:
                    raise InvalidMutexReleaseEncountered("Got an unknown value at release...!")

            except redis.exceptions.WatchError:
                if self._can_break(key, tries, is_release=True):
                    break

            # sleep a bit.
            sleep(self.spinlock_sleep_thresh)

        if tries > self.max_spinlock_tries:
            msg = f"Spinlock tries exceeded during release of request with tag: {res.tag if res else 'UNKNOWN'}."
            qlog.error(msg)
            raise SpinlockTriesExceeded(msg)

    def _generate_payload(self, val: QueryState) -> str:
        """
        Generate the payload to store in redis.

        Parameters
        ----------
        val: QueryState
            The query state to be stored in redis.

        Returns
        -------
        str
            The payload value.
        """
        return f"{self._tag},{val.value}"

    def _acquire(self):
        """
        Tries to acquire the mutex for the given query.

        Raises
        ------
        SpinlockTriesExceeded
            Is raised when we exceed the number of tries to "own" the query mutex.
        """
        key = self.get_key()

        # the current spinlock tries to get the Query mutex
        tries = 1
        force_unblock = False

        for _ in enumerate(range(self.max_spinlock_tries)):
            try:
                pipe = self._sess.pipeline()
                pipe.watch(key)

                res = self._unpack_value(self._get_redis_sess().get(key))

                if res is None or force_unblock:
                    qlog.debug("Blocking key with tag: %s, blocking was forced: %s", self._tag, force_unblock)
                    pipe.set(key, self._generate_payload(QueryState.BLOCKED), exat=self._get_expiry_unix_time())
                    pipe.execute()
                    qlog.debug("The key did not exist before, now its blocked by request with tag: %s.", self._tag)
                    break

                # clear everything in multi block, even if its empty from set ops
                pipe.execute()

                if self._mutex_value_match(res, QueryState.BLOCKED):
                    if self._tag_match(res):
                        qlog.debug(
                            "Query mutex can be released as tags match, tag: %s, spinlock tries: %s", res.tag, tries
                        )
                        break
                    if not self._has_exhausted_block_time(res):
                        qlog.debug(
                            "Query mutex is blocked by request with tag: %s, spinlock tries: %s", res.tag, tries
                        )
                        sleep(self.spinlock_sleep_thresh)
                    else:
                        qlog.debug(
                            "Query mutex was blocked for more than the allowed time (which was: %s seconds) "
                            "- force blocking it upon next try.",
                            self.max_block_time.total_seconds(),
                        )
                        force_unblock = True
                elif self._mutex_value_match(res, QueryState.COMPUTED):
                    qlog.debug("Query has already been computed for key: %s", self.get_key())
                    break
                else:
                    raise AtomicQueryInvalidStateException(f"Encountered an unexpected state value: {res}")
            except redis.exceptions.WatchError:
                if self._can_break(key, tries, is_release=False):
                    break

            tries += 1

        if tries > self.max_spinlock_tries:
            raise SpinlockTriesExceeded(
                f"Spinlock tries limit of {self.max_spinlock_tries} was exceeded for key {self.get_key()}"
            )

    def _has_exhausted_block_time(self, val: UnpackedValue) -> bool:
        """
        Checks if the mutex block has exceeded the allowed time per query.

        Parameters
        ----------
        val: UnpackedValue
            The unpacked value instance.

        Returns
        -------
        bool
            Returns `True` if the mutex was blocked for more than the allowed time or was `None`, `False` otherwise.
        """

        return val.timestamp is None or (datetime.now(tz=timezone.utc) - val.timestamp) > self.max_block_time

    def _can_break(self, key: str, tries: int, is_release: bool):
        """
        Function that checks if we are able to break from the spinlock.

        Parameters
        ----------
        key: str
            The key for the entry.
        tries: int
            The current spinlock tries.

        Returns
        -------
        bool
            Returns True if we are able to break, otherwise False.
        """
        res = self._unpack_value(self._get_redis_sess().get(key))
        mutex_stage = "release" if is_release else "acquisition"
        if res is None:
            raise InvalidMutexReleaseEncountered(
                f"Cannot have a null key at break check during {mutex_stage}, for key: {self.get_key()}"
            )

        if self._tag_match(res) and self._mutex_value_match(res, QueryState.BLOCKED):
            qlog.debug(
                "Query mutex value changed during its %s, but it was from us as tags match, tag: %s",
                mutex_stage,
                self._tag,
            )
            return True

        qlog.debug(
            "Query mutex value changed during its %s, attempting to get the mutex until spinlock tries is exhausted "
            "current: %s out of: %s.",
            mutex_stage,
            tries,
            self.max_spinlock_tries,
        )
        return False

    @abstractmethod
    def get_key(self) -> str:
        """
        Fetches the base key for the page.

        Returns
        -------
        str
            The key to store the value in redis.
        """
        raise NotImplementedError

    def delete_atomic_query_mutex_state(self) -> bool:
        """
        Attempt to delete a specific mutex state for a given result-set from the global state stored within redis.

        Returns
        -------
        bool
            Returns `True` if we managed to successfully delete the mutex state, `False` otherwise.
        """
        key = self.get_key()

        if (res := self._get_redis_sess().delete(key)) == 0:
            qlog.debug("Failed to delete mutex state for key: %s, potentially it does not exist", key)
        else:
            qlog.debug("Deleted successfully mutex state for key: %s", key)

        return res != 0

    def _get_redis_sess(self) -> redis.Redis:
        """
        Fetch or create a redis session based on the current parameters.

        Returns
        -------
        redis.Redis
            The redis instance to use.
        """
        if self._sess is None:
            raise AttributeError()

        return self._sess
