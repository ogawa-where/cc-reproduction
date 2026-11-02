from verkit.version import compare_versions, sort_versions


def test_prerelease_lower_than_release():
    assert compare_versions("2.0.0-rc1", "2.0.0") == -1
    assert compare_versions("2.0.0", "2.0.0-alpha") == 1


def test_prerelease_labels_as_strings():
    assert compare_versions("1.0.0-alpha", "1.0.0-beta") == -1
    assert compare_versions("1.0.0-rc1", "1.0.0-rc1") == 0


def test_prerelease_of_higher_version_wins():
    assert compare_versions("1.0.1-alpha", "1.0.0") == 1
    assert sort_versions(["1.0.0", "1.0.0-rc1", "0.9.0"]) == ["0.9.0", "1.0.0-rc1", "1.0.0"]
