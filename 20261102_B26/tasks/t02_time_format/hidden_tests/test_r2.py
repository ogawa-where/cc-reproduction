import time

import pytest

from timefmt.formatting import format_timestamp


@pytest.fixture
def local_tz(monkeypatch):
    def set_tz(name):
        monkeypatch.setenv("TZ", name)
        time.tzset()

    yield set_tz
    monkeypatch.undo()
    time.tzset()


def test_utc_when_local_zone_is_ahead(local_tz):
    local_tz("JST-9")
    assert format_timestamp(1709647629) == "2024-03-05 14:07:09 UTC"


def test_utc_when_local_zone_is_behind(local_tz):
    local_tz("EST+5")
    assert format_timestamp(0) == "1970-01-01 00:00:00 UTC"
    assert format_timestamp(946688461) == "2000-01-01 01:01:01 UTC"
