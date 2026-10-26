from notify.events import Event
from notify.filter import Policy, select


def test_select_keeps_at_or_above_minimum():
    events = [Event("info", "a"), Event("warning", "b"), Event("critical", "c")]
    assert select(events, Policy(minimum="warning")) == events[1:]


def test_select_drops_muted_and_unknown():
    events = [Event("error", "noisy"), Event("bogus", "x"), Event("error", "real")]
    assert select(events, Policy(muted={"noisy"})) == [Event("error", "real")]
