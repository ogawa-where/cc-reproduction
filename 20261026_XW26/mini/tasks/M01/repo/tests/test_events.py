import pytest

from notify.events import Event, EventError, parse_line, parse_lines


def test_parse_line():
    assert parse_line("error|disk full") == Event("error", "disk full")


def test_parse_line_lowercases_kind_and_keeps_pipes_in_message():
    assert parse_line("WARNING|a|b") == Event("warning", "a|b")


@pytest.mark.parametrize("bad", ["no separator", "|msg", "kind|", "  "])
def test_parse_line_rejects_bad_input(bad):
    with pytest.raises(EventError):
        parse_line(bad)


def test_parse_lines_skips_bad_lines():
    events = parse_lines(["info|ok", "", "broken", "error|bad"])
    assert [e.kind for e in events] == ["info", "error"]
