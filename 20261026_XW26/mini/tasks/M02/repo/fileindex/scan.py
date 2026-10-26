"""Walking a folder tree."""
from __future__ import annotations

import os
import os.path
from dataclasses import dataclass


class ScanError(ValueError):
    """Raised when the root cannot be scanned."""


@dataclass(frozen=True)
class Entry:
    path: str      # relative to the root, with forward slashes
    size: int


def scan(root: str) -> list[Entry]:
    """List every file under root, sorted by relative path."""
    if not os.path.isdir(root):
        raise ScanError("not a folder: " + root)
    entries: list[Entry] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            entries.append(Entry(path=rel, size=os.path.getsize(full)))
    entries.sort(key=lambda e: e.path)
    return entries


def extension(path: str) -> str | None:
    """The extension without the dot, or None when the file has none."""
    _, ext = os.path.splitext(os.path.basename(path))
    return ext[1:] if ext else None
