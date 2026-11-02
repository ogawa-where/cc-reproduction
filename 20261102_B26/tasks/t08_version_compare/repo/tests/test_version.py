from verkit.version import compare_versions, sort_versions


def test_compare_basic():
    assert compare_versions("1.2.3", "1.2.4") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_sort_basic():
    assert sort_versions(["1.3.0", "1.1.0", "1.2.0"]) == ["1.1.0", "1.2.0", "1.3.0"]
