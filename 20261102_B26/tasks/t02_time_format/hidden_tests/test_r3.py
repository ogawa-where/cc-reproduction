from timefmt.formatting import format_duration


def test_zero_units_omitted():
    assert format_duration(3600) == "1h"
    assert format_duration(61) == "1m 1s"
    assert format_duration(3605) == "1h 5s"
    assert format_duration(45) == "45s"


def test_zero_is_0s():
    assert format_duration(0) == "0s"


def test_no_days():
    assert format_duration(90000) == "25h"
    assert format_duration(90061) == "25h 1m 1s"
