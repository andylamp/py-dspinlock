"""Module that tests mutex state deletion functionality."""
from dspinlock import HashDSpinlock


def test_delete_mutex_state(hashable_string_factory):
    """Tests the mutex delete functionality."""
    the_obj = hashable_string_factory()
    with HashDSpinlock(the_obj) as dhash:
        print("This is a test query to see that this executes.")

    # now attempt to delete
    assert dhash.delete_atomic_query_mutex_state()
