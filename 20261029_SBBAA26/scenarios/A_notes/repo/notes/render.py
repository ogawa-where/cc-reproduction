from __future__ import annotations


def line(note: dict) -> str:
    tags = " ".join("#" + t for t in note.get("tags", []))
    return f"{note['id']:>4}  {note['created'][:10]}  {note['text']}" + (f"  {tags}" if tags else "")


def table(notes: list[dict]) -> str:
    return "\n".join(line(n) for n in notes)
