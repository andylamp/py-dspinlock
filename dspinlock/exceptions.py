"""Exceptions used in the kobodema application."""


class InvalidValueEncounteredDuringUnpacking(Exception):
    """Raised when the unpacked value of the mutex cannot be parsed."""


class RedisNotInitializedException(Exception):
    """Raised when redis instance is not initialised properly."""


class AtomicQueryInvalidStateException(Exception):
    """Raised when we encounter an invalid state during AtomicQuery execution."""


class SpinlockTriesExceeded(Exception):
    """Raised when we exhaust our spinlock tries due to query taking very long."""


class InvalidMutexReleaseEncountered(Exception):
    """Raised when we try to release a mutex that is not ours."""
