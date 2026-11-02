import pytest

from verkit.version import compare_versions


@pytest.mark.parametrize("bad", ["", "1..2", "a.b", "1.2.x", "1.2.", "1.0-"])
def test_malformed_raises(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0")
    with pytest.raises(ValueError):
        compare_versions("1.0", bad)


@pytest.mark.parametrize("bad", ["v1.0", "1.-2", "1.0 beta"])
def test_other_forms_raise(bad):
    with pytest.raises(ValueError):
        compare_versions(bad, "1.0")
