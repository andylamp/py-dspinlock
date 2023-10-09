# Distributed Spinlock

![linters](https://github.com/andylamp/py-dspinlock/workflows/lint/badge.svg)
![coverage](../coverage.svg)

## Introduction

This a simple, yet flexible implementation of a distributed spinlock mutex. This can be useful when you have many
stateless distributed services that are in contention for the same resource. For example, this can be reflected
when you want to avoid duplicate computations while a query is already executing.

*Note: the documentation in `readthedocs` is always generated against the latest released version, thus there might
be differences if you are using the checkout from `main` avenue to install.*

## Preliminaries

The implementation is based on `redis` and practically is the only required dependency in order to successfully
install the library. For more configuration options and usage directions please read on.

## Installation

To use the library, please install it as follows,

```bash
# assuming you are in a virtual environment
pip install py-dspilock
```

Any requirements will be installed automatically, but the minimum required version of `redis` client is set to
be `5.0.0`.

## Usage

Out of the box, the library provides a distributed spinlock implementation that can be used with _any_ object that
implements [`Hashable`][1]. Practically, this means that the object instance can be `hash`ed. For example,

```python
# a string is hashable,
s = "example"
# its hash value can be extracted as such,
s_hash = hash(s)
```

Thus, a practical example that you can use out of the box is the following,

```python
"""A basic example of how to use the HashDSpinlock."""

from dspinlock import HashDSpinlock

if __name__ == "__main__":
    with HashDSpinlock("example"):
        print("executed task_id: 1")
```

If you do not supply any arguments, then the default parameters are used. Meaning that the following hold,

- `redis` connection gets created with the predefined parameters (host: `localhost`, db: `1`, port: `6379`)
- `fail_if_key_exists`: is set to `False`
- `cached_if_computed`: is set to `False`.

### Parameterising `redis` connection

Ideally, the `redis` connection should not be created for every call we make to the spinlock mutex. Thus, ideally,
we should be caching that and passing it as an argument as such,

```python
"""An example of how to use the HashDSpinlock with an existing `redis` connection."""

from dspinlock import HashDSpinlock
from dspinlock.utils import create_redis_conn

# using default parameters
sess = create_redis_conn()

if __name__ == "__main__":
    with HashDSpinlock("example", sess=sess):
        print("executed task_id: 1")
```

If no arguments are supplied to `create_redis_conn` method, then a connection with the default parameters is created.
To parameterise it, we can use the following,

```python
"""An example of how to use the HashDSpinlock with an existing parameterised `redis` connection."""

from dspinlock import HashDSpinlock
from dspinlock.utils import create_redis_conn, RedisParameters

params = RedisParameters(
    redis_host="localhost",
    rdb=0,
    port=6379,
    ssl=False,
    socket_connect_timeout=2,
    decode_responses=True
)

# using default parameters
sess = create_redis_conn(params)

if __name__ == "__main__":
    with HashDSpinlock("example", sess=sess):
        print("executed task_id: 1")
```

For more information, please check the source code at the [link][2].

### Extending the base class to fit your needs

While a default Spinlock is supplied, it is very common that you might want to subclass it in order to customise
its functionality. There are two avenues to do that, you can subclass `HashDSpinlock` directly, or you can
subclass its base abstract class `DSpinlockBase`. Most of the functionality is contained in the base abstract class,
hence you need to only implement the methods shown in `HashDSpinlock` and tweak any of the base class values such as,

- `max_spinlock_tries`: The spinlock max retries, by default 10 tries.
- `spinlock_sleep_thresh`: The spinlock sleep threshold, by default 0.5 seconds.
- `expire_at_timedelta`: Sets timedelta from creation that the mutex expires, by default 1 hour.
- `max_block_time`: The max block time allowed for a query mutex to be held, if not released it's forcefully unblocked.

#### Extending `HashDSpinLock` to tweak above values

```python
"""An example of how to subclass `HashDSpinlock` while tweaking its base attributes."""
from dspinlock import HashDSpinlock

class CustomSpinlock(HashDSpinlock):
    """Custom class that overrides the basic variables"""
    spinlock_sleep_thresh: float = 0.1
    """Tweak the threshold for spinlock sleep."""

if __name__ == "__main__":
    with CustomSpinlock("example"):
        print("executed task_id: 1")
```

### Enable logging

The library uses a custom logger in order to provide diagnostic information. To enable the logger, to do two things.
Firstly you need to set the environment variable - using any value - with the key: `SL_LOG_ENABLED`. After, you have
to set your basic logger to accept at least `DEBUG` level messages, as all diagnostic ones are set to that level.

The code snippet that perform that is shown below,

```python
import logging

from dspinlock import HashDSpinlock
from dspinlock.consts import SL_LOG_LEVEL

# ensure your basic logger exists
logging.basicConfig(level=SL_LOG_LEVEL)

if __name__ == "__main__":
    # now you see some debug messages in the default format of the library.
    with HashDSpinlock("asdf"):
        print("executed task_id: 1")
```

[1]: https://docs.python.org/3/library/collections.abc.html?highlight=hashable#collections.abc.Hashable
[2]: https://github.com/andylamp/py-dspinlock/blob/main/dspinlock/utils.py
