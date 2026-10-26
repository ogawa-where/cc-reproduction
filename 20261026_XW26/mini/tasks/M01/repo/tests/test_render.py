from notify.events import Event
from notify.render import Message, render, render_all


def test_render_formats_text_and_urgency():
    assert render(Event("error", "disk full")) == Message("[x] ERROR: disk full", True)
    assert render(Event("info", "hello")).urgent is False


def test_render_all_keeps_order():
    texts = [m.text for m in render_all([Event("info", "a"), Event("warning", "b")])]
    assert texts == ["[i] INFO: a", "[!] WARNING: b"]
