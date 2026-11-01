"""python -m pipeline.report DATA.csv [--out FILE]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pipeline import aggregate, load


def render(rows: list[dict]) -> str:
    lines = ["# Sales report", "", "## Revenue by region"]
    for region, rev in sorted(aggregate.revenue_by_region(rows).items()):
        lines.append(f"- {region}: {rev:.2f}")
    lines += ["", "## Units by product"]
    for product, units in sorted(aggregate.units_by_product(rows).items()):
        lines.append(f"- {product}: {units}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="report")
    p.add_argument("data")
    p.add_argument("--out")
    args = p.parse_args(argv)
    text = render(load.read_rows(Path(args.data)))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
