"""JSON-file storage for notes. Shared with the sync service: keep the format stable."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path("notes.json")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load(path: Path = DEFAULT_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(notes: list[dict], path: Path = DEFAULT_PATH) -> None:
    path.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")


def add(notes: list[dict], text: str) -> dict:
    note = {"id": max((n["id"] for n in notes), default=0) + 1, "text": text, "created": _now(), "tags": []}
    notes.append(note)
    return note


def get(notes: list[dict], note_id: int) -> dict:
    for n in notes:
        if n["id"] == note_id:
            return n
    raise KeyError(note_id)
