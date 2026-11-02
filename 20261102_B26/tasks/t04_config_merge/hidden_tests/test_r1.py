from confmerge.merge import deep_merge


def test_disjoint_keys_union():
    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_scalar_replaces_dict_and_dict_replaces_scalar():
    assert deep_merge({"a": {"x": 1}}, {"a": 5}) == {"a": 5}
    assert deep_merge({"a": 5}, {"a": {"x": 1}}) == {"a": {"x": 1}}


def test_lists_replaced_not_concatenated():
    assert deep_merge({"tags": [1, 2]}, {"tags": [3]}) == {"tags": [3]}
