from confmerge.merge import deep_merge


def test_none_removes_top_level_key():
    assert deep_merge({"a": 1, "b": 2}, {"a": None}) == {"b": 2}


def test_none_removes_nested_key():
    base = {"db": {"host": "h", "password": "x"}}
    assert deep_merge(base, {"db": {"password": None}}) == {"db": {"host": "h"}}


def test_none_for_missing_key_is_absent():
    assert deep_merge({"a": 1}, {"zzz": None}) == {"a": 1}
