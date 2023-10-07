"""Module that implements the hashable distributed spinlock."""
from collections.abc import Hashable
from datetime import datetime, timezone
from uuid import uuid4

from .base import DSpinlockBase, UnpackedValue
from .exceptions import InvalidValueEncounteredDuringUnpacking


# pylint: disable=too-few-public-methods
class HashDSpinlock(DSpinlockBase):
    """A Hash based Distributed Spinlock, which works on any object that implements `Hashable`."""

    def get_key(self) -> str:
        """
        Gets the key for the entry. For this particular implementation, it has the following format,

        key = `{self._key_prefix}{self.tag_sep}{self._obj_hash}`

        Where the following values normally hold - unless overriden,

        - `_key_prefix`: `dspinlock`
        - `_obj_hash`: the result of using the `hash` function with the object instance - _i.e._: `hash(obj)`

        By default, each segment of the key is seperated by a comma - though internally this can be configured by
        adjusting the `_key_sep` variable.

        Note, that the `_key_prefix` value can also be adjusted, but as mentioned above the default is: `dspinlock`.

        Returns
        -------
        str
            The entry key.
        """
        return f"{self._key_prefix}{self._key_sep}{self._obj_hash}"

    def _set_tag(self, obj: Hashable | None = None):
        """
        Sets the tag for the given object. It is one of the primary functions to override. This is because the tag
        should be instance dependent and unique across instances.

        For this implementation, the tag is set to be equal to the following - in that order - each value being
        seperated by comma,

            - a UUID4 to be the random identifier for this object.
            - the timestamp of creation,

        The above combination has very low probability - but not zero - to clash with another instance.

        Parameters
        ----------
        obj: Hashable | None = None
            The object instance to set the tag for - by default it is `None`.
        """
        return f"{uuid4()}{self._value_sep}{datetime.now(tz=timezone.utc).isoformat()}"

    def _unpack_value(self, value: str | None) -> UnpackedValue | None:
        """
        Unpacks the value from `redis`. This is class specific as it depends on how your tag is formatted.

        For this implementation the stored value has the following format,

            - uuid4: the instance uuid4,
            - datetime ts: the datetime timestamp,
            - mutex value: the mutex current value

        By default, each segment of the value is seperated by a comma - though internally this can be configured by
        adjusting the `_value_sep` variable.

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

        tokens = value.split(self._value_sep)
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
