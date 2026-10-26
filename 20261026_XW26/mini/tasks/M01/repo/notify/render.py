"""Rendering of events as channel messages."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from notify.events import Event

logger = logging.getLogger(__name__)

ICONS = {"info": "i", "warning": "!", "error": "x", "critical": "xx"}


@dataclass(frozen=True)
class Message:
    text: str
    urgent: bool


def render(event: Event) -> Message:
    icon = ICONS.get(event.kind, "?")
    text = f"[{icon}] {event.kind.upper()}: {event.message}"
    urgent = event.kind in ("error", "critical")
    logger.debug(f"rendered {event.kind} as urgent={urgent}")
    return Message(text=text, urgent=urgent)


def render_all(events: list[Event]) -> list[Message]:
    messages = [render(e) for e in events]
    logger.info(f"rendered {len(messages)} messages")
    return messages
