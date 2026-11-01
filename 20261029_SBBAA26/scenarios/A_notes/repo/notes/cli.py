"""Command line interface: python -m notes.cli <command> ..."""
from __future__ import annotations

import argparse
import sys

from notes import render, storage


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="notes")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="add a note")
    a.add_argument("text")
    sub.add_parser("list", help="list notes")
    s = sub.add_parser("show", help="show one note")
    s.add_argument("id", type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    notes = storage.load()
    if args.cmd == "add":
        note = storage.add(notes, args.text)
        storage.save(notes)
        print(render.line(note))
    elif args.cmd == "list":
        print(render.table(notes))
    elif args.cmd == "show":
        try:
            print(render.line(storage.get(notes, args.id)))
        except KeyError:
            print(f"no note {args.id}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
