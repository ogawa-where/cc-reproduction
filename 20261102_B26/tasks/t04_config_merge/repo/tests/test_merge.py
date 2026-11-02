from confmerge.merge import deep_merge


def test_flat_override_wins():
    assert deep_merge({"a": 1, "b": 2}, {"b": 3}) == {"a": 1, "b": 3}


def test_nested_merge():
    base = {"db": {"host": "localhost", "port": 5432}}
    override = {"db": {"port": 6543}}
    assert deep_merge(base, override) == {"db": {"host": "localhost", "port": 6543}}
