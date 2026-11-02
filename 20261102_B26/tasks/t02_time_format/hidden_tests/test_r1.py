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


def test_known_timestamp(local_tz):
    local_tz("UTC0")
    assert format_timestamp(1709647629) == "2024-03-05 14:07:09 UTC"


def test_fraction_dropped(local_tz):
    local_tz("UTC0")
    assert format_timestamp(1709647629.987) == "2024-03-05 14:07:09 UTC"


def test_zero_padding(local_tz):
    local_tz("UTC0")
    assert format_timestamp(946688461) == "2000-01-01 01:01:01 UTC"
