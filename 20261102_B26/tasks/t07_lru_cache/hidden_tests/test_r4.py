import pytest

from lrucache.cache import LRUCache


def test_zero_capacity_rejected():
    with pytest.raises(ValueError):
        LRUCache(0)


def test_negative_capacity_rejected():
    with pytest.raises(ValueError):
        LRUCache(-3)
