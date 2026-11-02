import copy

from confmerge.merge import deep_merge


def test_inputs_not_modified():
    base = {"a": {"b": 1, "c": [1, 2]}, "d": 4, "e": 5}
    override = {"a": {"b": 2}, "d": None, "f": {"g": 1}}
    base_before, override_before = copy.deepcopy(base), copy.deepcopy(override)
    deep_merge(base, override)
    assert base == base_before
    assert override == override_before


def test_result_independent_of_base():
    base = {"a": {"b": 1}, "items": [1, 2]}
    result = deep_merge(base, {"c": 3})
    result["a"]["b"] = 99
    result["items"].append(3)
    assert base == {"a": {"b": 1}, "items": [1, 2]}


def test_result_independent_of_override():
    override = {"a": {"b": 1}, "items": [1]}
    result = deep_merge({}, override)
    result["a"]["b"] = 99
    result["items"].append(2)
    assert override == {"a": {"b": 1}, "items": [1]}
