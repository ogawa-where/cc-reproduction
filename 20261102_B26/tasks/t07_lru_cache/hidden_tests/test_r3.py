from lrucache.cache import LRUCache


def test_get_refreshes_recency():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)
    assert "a" in cache
    assert "b" not in cache


def test_put_existing_refreshes_and_does_not_evict():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("a", 10)
    assert len(cache) == 2
    assert "b" in cache
    cache.put("c", 3)
    assert cache.get("a") == 10
    assert "b" not in cache


def test_membership_does_not_refresh():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert "a" in cache
    cache.put("c", 3)
    assert "a" not in cache
    assert "b" in cache
