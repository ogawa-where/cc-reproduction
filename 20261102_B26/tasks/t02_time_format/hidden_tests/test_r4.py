import pytest

from timefmt.formatting import format_duration


def test_negative_raises():
    with pytest.raises(ValueError):
        format_duration(-1)


def test_large_negative_raises():
    with pytest.raises(ValueError):
        format_duration(-3725)
