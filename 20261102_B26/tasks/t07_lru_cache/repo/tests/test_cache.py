from lrucache.cache import LRUCache


def test_put_and_get():
    cache = LRUCache(2)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_missing_key_returns_default():
    cache = LRUCache(2)
    assert cache.get("nope") is None
    assert cache.get("nope", 0) == 0
