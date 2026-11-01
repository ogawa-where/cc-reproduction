from __future__ import annotations

from collections import defaultdict


def revenue_by_region(rows: list[dict]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in rows:
        out[r["region"]] += r["units"] * r["unit_price"]
    return dict(out)


def units_by_product(rows: list[dict]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for r in rows:
        out[r["product"]] += r["units"]
    return dict(out)
