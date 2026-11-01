#!/usr/bin/env python3
"""E3 summary: P(recursion) per shape x position x wording, with dP against the matching no-image baseline.
Usage: python summarize_e3.py runs/samples-e3-opus.jsonl"""
from __future__ import annotations

import collections
import json
import math
import sys


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main():
    ss = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    cells = collections.defaultdict(list)
    for s in ss:
        cells[(s["shape"], s["position"], s["wording"])].append(s)
    def p_of(key):
        lst = [s for s in cells.get(key, []) if s["label"] in ("recursive", "iterative", "other")]
        k = sum(1 for s in lst if s["label"] == "recursive")
        return k, len(lst)
    positions = ["first", "default", "after"]
    wordings = ["explicit", "neutral", "ordinary"]
    shapes = [sh for sh in ["none", "spiral", "branching_arrows", "heart"] if any(c[0] == sh for c in cells)]
    print(f"{len(ss)} samples. Cells: P(recursion) = recursive/n  [dP vs no-image baseline of the same position x wording]")
    print(f"{'shape':17s} {'wording':9s} " + " ".join(f"{p:>22s}" for p in positions))
    for sh in shapes:
        for wo in wordings:
            row = []
            for po in positions:
                k, n = p_of((sh, po, wo))
                if n == 0:
                    row.append(f"{'-':>22s}"); continue
                p = k / n
                bk, bn = p_of(("none", po, wo))
                d = f" [{p - bk / bn:+.2f}]" if sh != "none" and bn else ""
                lo, hi = wilson(k, n)
                row.append(f"{p:5.2f} ({k:>2d}/{n:<2d}){d:>8s}")
            print(f"{sh:17s} {wo:9s} " + " ".join(f"{c:>22s}" for c in row))
    errors = sum(1 for s in ss if s["label"] == "error")
    if errors:
        print(f"errors: {errors}")


if __name__ == "__main__":
    main()
