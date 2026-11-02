from confmerge.merge import deep_merge


def test_three_levels():
    base = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
    override = {"a": {"b": {"d": 20, "f": 30}}}
    assert deep_merge(base, override) == {"a": {"b": {"c": 1, "d": 20, "f": 30}, "e": 3}}


def test_empty_override_and_empty_base():
    assert deep_merge({"a": {"b": 1}}, {}) == {"a": {"b": 1}}
    assert deep_merge({}, {"a": {"b": 1}}) == {"a": {"b": 1}}
