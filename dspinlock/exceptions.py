"""Exceptions used within the library."""


class InvalidValueEncounteredDuringUnpacking(Exception):
    """Raised when the unpacked value of the mutex cannot be parsed."""


class RedisNotInitializedException(Exception):
    """Raised when `redis` instance is not initialised properly."""


class AtomicQueryInvalidStateException(Exception):
    """Raised when we encounter an invalid state during AtomicQuery execution."""


class SpinlockTriesExceeded(Exception):
    """Raised when we exhaust our spinlock tries due to query taking very long."""


class InvalidMutexReleaseEncountered(Exception):
    """Raised when we try to release a mutex that is not ours."""


class FailIfKeyExistsIsEnabled(Exception):
    """Raised when we try to acquire a lock when the key already exists and the flag to fail is so is `True`"""


class ProvidedObjectIsNotHashable(Exception):
    """Raised when the object passed does not implement `Hashable`."""
