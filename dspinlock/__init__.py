"""Module that imports helpers."""
import logging
import os
from typing import TypeAlias

from .base import DSpinlockBase
from .consts import SL_LOG_ENABLED, SL_LOG_FORMAT, SL_LOG_LEVEL, SL_LOG_TAG
from .exceptions import (
    AtomicQueryInvalidStateException,
    FailIfKeyExistsIsEnabled,
    InvalidMutexReleaseEncountered,
    InvalidValueEncounteredDuringUnpacking,
    ProvidedObjectIsNotHashable,
    RedisNotInitializedException,
    SpinlockTriesExceeded,
)
from .hash_dspinlock import HashDSpinlock

# put the type alias for the logging type
HandlerType: TypeAlias = logging.StreamHandler | logging.NullHandler

__all__ = [
    "DSpinlockBase",
    "HashDSpinlock",
    "AtomicQueryInvalidStateException",
    "InvalidMutexReleaseEncountered",
    "RedisNotInitializedException",
    "SpinlockTriesExceeded",
    "InvalidValueEncounteredDuringUnpacking",
    "FailIfKeyExistsIsEnabled",
    "ProvidedObjectIsNotHashable",
]

# enable logging, if we have the env flag up we report in stdout, otherwise
# we use `NullHandler`.
handler: HandlerType
if SL_LOG_ENABLED in os.environ:
    handler = logging.StreamHandler()
else:
    handler = logging.NullHandler()

# configure the target handler
if isinstance(handler, logging.StreamHandler):
    handler.setLevel(SL_LOG_LEVEL)
    handler.setFormatter(SL_LOG_FORMAT)

# get a logger by the specified name and attach its handler
logging.getLogger(SL_LOG_TAG).addHandler(handler)
