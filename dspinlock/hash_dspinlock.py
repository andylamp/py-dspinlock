"""Module that implements the hashable distributed spinlock."""
from typing import Any

from .base import DSpinlockBase


# pylint: disable=too-few-public-methods
class HashDSpinlock(DSpinlockBase):
    """A Hash based Distributed Spinlock, which works on any object that implements hashable."""

    def get_key(self) -> str:
        """
        Gets the key for the entry.

        Returns
        -------
        str
            The entry key.
        """
        return ""

    def _set_tag(self, obj: Any):
        """
        Sets the tag for the given object.

        Parameters
        ----------
        obj: Any
            The object instance to set the tag for.
        """
        self._tag = ""
