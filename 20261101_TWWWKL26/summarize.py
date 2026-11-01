#!/usr/bin/env python3
"""P(recursion) per condition and the steering effect dP relative to baseline.
Usage: python summarize.py runs/samples-sonnet.jsonl [more files...] [--by-shape] [--by-color]"""
from __future__ import annotations

import argparse
import collections
import json
import math

PAPER = {"baseline": "Opus 4.7: 0.00, GPT-5.4: 0.00, Gemini 3.1 Pro: 0.40",
         "image:heart:red": "Opus 4.7 dP=+1.0, GPT-5.4 dP=+1.0",
         "text:recursive": "dP=+1.0 (Claude), +0.6 (Gemini)", "noise": "dP=0.0 (Claude, GPT), ~-0.1 (Gemini)",
         "caption:heart:red": "captions: minimal to no steering (r=-0.05 vs images for Claude)"}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--by-shape", action="store_true")
    ap.add_argument("--by-color", action="store_true")
    args = ap.parse_args()
    samples = [json.loads(l) for p in args.paths for l in open(p, encoding="utf-8") if l.strip()]
    by_model = collections.defaultdict(list)
    for s in samples:
        by_model[s.get("model", "?")].append(s)
    for model, ss in by_model.items():
        print(f"model: {model}  ({len(ss)} samples)")
        conds = collections.defaultdict(list)
        for s in ss:
            conds[s["condition"]].append(s)
        base = conds.get("baseline", [])
        pb = sum(1 for s in base if s.get("label") == "recursive") / len(base) if base else None
        print(f"  {'condition':28s} {'rec/iter/other/err':>20s} {'P(rec)':>7s} {'95% CI':>14s} {'dP':>6s}   paper")
        rows = []
        for c, lst in conds.items():
            k = sum(1 for s in lst if s.get("label") == "recursive")
            it = sum(1 for s in lst if s.get("label") == "iterative")
            ot = sum(1 for s in lst if s.get("label") == "other")
            er = sum(1 for s in lst if s.get("label") in ("error", None) or s.get("error"))
            n = k + it + ot
            p = k / n if n else 0
            lo, hi = wilson(k, n)
            d = f"{p - pb:+.2f}" if pb is not None and c != "baseline" else ""
            rows.append((c, k, it, ot, er, p, lo, hi, d))
        order = {"baseline": 0, "text:recursive": 1, "text:iterative": 1, "noise": 2}
        rows.sort(key=lambda r: (order.get(r[0], 3), -r[5]))
        for c, k, it, ot, er, p, lo, hi, d in rows:
            print(f"  {c:28s} {k:>4d}/{it:<4d}/{ot:<3d}/{er:<3d} {p:7.2f} [{lo:5.2f}, {hi:5.2f}] {d:>6s}   {PAPER.get(c, '')}")
        if args.by_shape or args.by_color:
            agg = collections.defaultdict(lambda: [0, 0])
            for c, lst in conds.items():
                parts = c.split(":")
                if parts[0] != "image":
                    continue
                key = parts[1] if args.by_shape else parts[2]
                for s in lst:
                    if s.get("label") in ("recursive", "iterative", "other"):
                        agg[key][1] += 1
                        agg[key][0] += s["label"] == "recursive"
            print(f"  --- mean P(recursion) by {'shape' if args.by_shape else 'color'} (dP vs baseline {pb if pb is not None else 'n/a'}) ---")
            for key, (k, n) in sorted(agg.items(), key=lambda kv: -kv[1][0] / max(kv[1][1], 1)):
                p = k / n if n else 0
                print(f"  {key:20s} {k:>4d}/{n:<4d} {p:6.2f}" + (f"  dP {p - pb:+.2f}" if pb is not None else ""))
        print()


if __name__ == "__main__":
    main()
