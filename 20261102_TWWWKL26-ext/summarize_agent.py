#!/usr/bin/env python3
"""Summarise run_agent.py output: per cell the label counts, P(recursion) with a Wilson 95% interval
(over recursive + iterative + other, errors and 'unimplemented' excluded), dP against the baseline cell
none:silent:ordinary:none, the image-read rate, mean tool calls and total cost.
When a (cell, sample) appears more than once (resumed runs), the last non-error record wins."""
from __future__ import annotations

import argparse
import json
import math

BASELINE = "none:silent:ordinary:none"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def load(paths):
    recs = {}
    for path in paths:
        for line in open(path, encoding="utf-8"):
            try:
                s = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (s.get("model"), s["cell"], s["sample"])
            ok = not s.get("error") and s.get("label") != "error"
            if ok or key not in recs or recs[key].get("error"):
                recs[key] = s
    return list(recs.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    recs = load(args.paths)
    groups = {}
    for s in recs:
        groups.setdefault((s.get("model"), s["cell"]), []).append(s)
    base_p = {}
    rows = []
    for (model, cell), ss in sorted(groups.items()):
        cnt = {k: 0 for k in ("recursive", "iterative", "other", "unimplemented", "error")}
        for s in ss:
            lab = "error" if s.get("error") else s.get("label", "error")
            cnt[lab if lab in cnt else "other"] += 1
        n = cnt["recursive"] + cnt["iterative"] + cnt["other"]
        p = cnt["recursive"] / n if n else float("nan")
        ok = [s for s in ss if not s.get("error")]
        rows.append((model, cell, cnt, n, p, wilson(cnt["recursive"], n),
                     sum(bool(s.get("image_read")) for s in ok) / len(ok) if ok else float("nan"),
                     sum(s.get("tool_calls") or 0 for s in ok) / len(ok) if ok else float("nan"),
                     sum(s.get("cost_usd") or 0 for s in ss)))
        if cell == BASELINE:
            base_p[model] = p
    hdr = (f"{'model':<7} {'cell':<40} {'rec':>4} {'iter':>4} {'oth':>4} {'unimp':>5} {'err':>4} "
           f"{'P(rec)':>7} {'95% CI':>15} {'dP':>7} {'img_read':>8} {'tools':>6} {'cost$':>8}")
    print(hdr)
    print("-" * len(hdr))
    for model, cell, cnt, n, p, (lo, hi), rd, tc, cost in rows:
        bp = base_p.get(model)
        dp = f"{p - bp:+.2f}" if bp is not None and n else "   -"
        print(f"{model:<7} {cell:<40} {cnt['recursive']:>4} {cnt['iterative']:>4} {cnt['other']:>4} "
              f"{cnt['unimplemented']:>5} {cnt['error']:>4} {p:>7.2f} {f'[{lo:.2f}, {hi:.2f}]':>15} {dp:>7} "
              f"{rd:>8.2f} {tc:>6.1f} {cost:>8.2f}")
    if not base_p:
        print(f"(no baseline cell {BASELINE}; dP not computed)")


if __name__ == "__main__":
    main()
