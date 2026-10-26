"""Lookups by file name."""
from __future__ import annotations

import os.path

from fileindex.scan import Entry


def find_by_name(entries: list[Entry], name: str) -> Entry | None:
    """The first entry whose base name equals name, or None."""
    for entry in entries:
        if os.path.basename(entry.path) == name:
            return entry
    return None


def find_all_by_name(entries: list[Entry], name: str) -> list[Entry]:
    return [e for e in entries if os.path.basename(e.path) == name]
