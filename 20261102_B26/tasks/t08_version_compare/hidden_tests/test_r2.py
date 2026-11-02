from verkit.version import compare_versions, sort_versions


def test_trailing_zero_equal():
    assert compare_versions("1.2", "1.2.0") == 0
    assert compare_versions("1.2.0.0", "1.2") == 0
    assert compare_versions("3", "3.0.0") == 0


def test_shorter_vs_longer_nonzero():
    assert compare_versions("1.2", "1.2.1") == -1
    assert compare_versions("2", "1.9.9") == 1


def test_sort_keeps_order_of_equal_versions():
    assert sort_versions(["1.2.0", "1.0", "1.2", "1"]) == ["1.0", "1", "1.2.0", "1.2"]
