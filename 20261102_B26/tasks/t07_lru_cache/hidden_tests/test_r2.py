from lrucache.cache import LRUCache


def test_oldest_evicted():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert "a" not in cache
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert len(cache) == 2


def test_eviction_sequence():
    cache = LRUCache(3)
    for i in range(6):
        cache.put(i, i * 10)
    assert len(cache) == 3
    assert [k for k in range(6) if k in cache] == [3, 4, 5]


def test_capacity_one():
    cache = LRUCache(1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" not in cache
    assert cache.get("b") == 2
