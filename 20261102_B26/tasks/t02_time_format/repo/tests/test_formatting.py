from timefmt.formatting import format_duration, format_timestamp


def test_timestamp_epoch():
    assert format_timestamp(0) == "1970-01-01 00:00:00 UTC"


def test_duration_all_units():
    assert format_duration(3725) == "1h 2m 5s"
