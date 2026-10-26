"""Parsing of event log lines."""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

KINDS = ("info", "warning", "error", "critical")


class EventError(ValueError):
    """Raised for a log line that cannot be read."""


@dataclass(frozen=True)
class Event:
    kind: str
    message: str


def parse_line(line: str) -> Event:
    """Parse one `kind|message` line into an Event."""
    text = line.strip()
    if "|" not in text:
        raise EventError(f"missing '|' separator in {text!r}")
    kind, message = text.split("|", 1)
    kind = kind.strip().lower()
    message = message.strip()
    if not kind:
        raise EventError(f"empty kind in {text!r}")
    if not message:
        raise EventError(f"empty message in {text!r}")
    logger.debug(f"parsed event kind={kind} message={message!r}")
    return Event(kind=kind, message=message)


def parse_lines(lines: list[str]) -> list[Event]:
    """Parse every non-blank line; unreadable lines are skipped with a warning."""
    events: list[Event] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            events.append(parse_line(line))
        except EventError as exc:
            logger.warning(f"line {number} skipped: {exc}")
    return events
