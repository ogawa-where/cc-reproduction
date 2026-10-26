"""Grouping of scanned entries by extension."""
from __future__ import annotations

from fileindex.scan import Entry, extension

NO_EXTENSION = "(none)"


def by_extension(entries: list[Entry]) -> dict[str, list[Entry]]:
    groups: dict[str, list[Entry]] = {}
    for entry in entries:
        key = extension(entry.path) or NO_EXTENSION
        groups.setdefault(key, []).append(entry)
    return groups


def counts(entries: list[Entry]) -> dict[str, int]:
    return {ext: len(group) for ext, group in by_extension(entries).items()}


def largest(entries: list[Entry]) -> Entry | None:
    """The largest entry, or None when there are no entries."""
    if not entries:
        return None
    return max(entries, key=lambda e: (e.size, e.path))
