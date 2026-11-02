from verkit.version import compare_versions, sort_versions


def test_numeric_not_lexicographic():
    assert compare_versions("1.10", "1.9") == 1
    assert compare_versions("1.9", "1.10") == -1
    assert compare_versions("10.0.0", "9.99.99") == 1


def test_return_values():
    assert compare_versions("3.4", "3.4") == 0
    assert compare_versions("0.1", "0.2") == -1


def test_sort_returns_new_sorted_list():
    data = ["1.10.0", "1.2.0", "1.9.0", "0.9.9"]
    result = sort_versions(data)
    assert result == ["0.9.9", "1.2.0", "1.9.0", "1.10.0"]
    assert data == ["1.10.0", "1.2.0", "1.9.0", "0.9.9"]
