"""python -m ssg.build CONTENT_DIR OUT_DIR"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ssg import markdown

TEMPLATE = "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>{title}</title></head>\n<body>\n{body}</body></html>\n"


def page_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def build(content: Path, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for src in sorted(content.glob("*.md")):
        md = src.read_text(encoding="utf-8")
        dst = out / (src.stem + ".html")
        dst.write_text(TEMPLATE.format(title=page_title(md, src.stem), body=markdown.to_html(md)), encoding="utf-8")
        written.append(dst)
    return written


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build")
    p.add_argument("content")
    p.add_argument("out")
    a = p.parse_args(argv)
    for path in build(Path(a.content), Path(a.out)):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
