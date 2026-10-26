"""Selection of events worth alerting on."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from notify.events import KINDS, Event

logger = logging.getLogger(__name__)


@dataclass
class Policy:
    minimum: str = "warning"
    muted: set[str] = field(default_factory=set)

    def rank(self, kind: str) -> int:
        return KINDS.index(kind) if kind in KINDS else -1


def select(events: list[Event], policy: Policy) -> list[Event]:
    """Return the events at or above the policy's minimum kind, minus muted messages."""
    floor = policy.rank(policy.minimum)
    kept: list[Event] = []
    for event in events:
        rank = policy.rank(event.kind)
        if rank < 0:
            logger.warning(f"unknown kind {event.kind!r} dropped")
            continue
        if rank < floor:
            continue
        if event.message in policy.muted:
            logger.info(f"muted message dropped: {event.message!r}")
            continue
        kept.append(event)
    logger.info(f"kept {len(kept)} of {len(events)} events")
    return kept
