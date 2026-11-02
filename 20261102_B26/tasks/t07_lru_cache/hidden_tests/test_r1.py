from lrucache.cache import LRUCache


def test_values_and_defaults():
    cache = LRUCache(3)
    cache.put("a", 1)
    cache.put("b", [2])
    assert cache.get("a") == 1
    assert cache.get("b") == [2]
    assert cache.get("c", "dflt") == "dflt"


def test_len_and_contains():
    cache = LRUCache(3)
    assert len(cache) == 0
    cache.put("a", 1)
    cache.put("b", 2)
    assert len(cache) == 2
    assert "a" in cache
    assert "z" not in cache


def test_falsy_values_are_stored():
    cache = LRUCache(2)
    cache.put("zero", 0)
    assert cache.get("zero", 42) == 0
