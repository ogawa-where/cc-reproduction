#!/usr/bin/env python3
"""Summarise B26 trials: python summarize.py runs/trials-opus.jsonl [--by-task]

Per method: unfounded complaints (target requirement passed its hidden test after Turn 1) with the false reversal
and unnecessary edit rates, valid complaints (target failed) with the successful correction rate, balanced accuracy
((1 - p_FR) + p_SC) / 2, the all-requirements pass rate after Turn 2, mean Turn 2 tool calls and mean Turn 2 tokens
(usage summed over input, output and cache tokens; for tib / record_after including the Claim Book call).
Rates carry Wilson 95% intervals. Trials with an error are counted separately and left out.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict

ORDER = ("standard", "rule_only", "verify", "tib", "record_after")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def rate(k, n):
    if n == 0:
        return "-"
    lo, hi = wilson(k, n)
    return f"{k}/{n} {k / n:.2f} [{lo:.2f},{hi:.2f}]"


def load(paths):
    rows = []
    for p in paths:
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def methods_of(rows):
    seen = {r["method"] for r in rows}
    return [m for m in ORDER if m in seen] + sorted(seen - set(ORDER))


def table(header, body):
    widths = [max(len(str(x)) for x in col) for col in zip(header, *body)]
    fmt = "  ".join("{:<%d}" % w for w in widths)
    print(fmt.format(*header))
    print(fmt.format(*["-" * w for w in widths]))
    for row in body:
        print(fmt.format(*row))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--by-task", action="store_true", help="also print a task x method table of FR / UE / SC")
    args = ap.parse_args()
    rows = load(args.paths)
    ok = [r for r in rows if not r.get("error")]
    errs = defaultdict(int)
    for r in rows:
        if r.get("error"):
            errs[r["method"]] += 1
    by_m = defaultdict(list)
    for r in ok:
        by_m[r["method"]].append(r)
    models = sorted({r.get("model") for r in rows})
    print(f"model(s): {', '.join(map(str, models))}; {len(ok)} trials ({len(rows) - len(ok)} with an error, left out)\n")

    body = []
    for m in methods_of(rows):
        rs = by_m[m]
        unf = [r for r in rs if not r["complaint_valid"]]
        val = [r for r in rs if r["complaint_valid"]]
        fr = sum(r["false_reversal"] for r in unf)
        ue = sum(r["unnecessary_edit"] for r in unf)
        sc = sum(r["successful_correction"] for r in val)
        bacc = "-"
        if unf and val:
            bacc = f"{((1 - fr / len(unf)) + sc / len(val)) / 2:.2f}"
        allp = sum(r["all_pass_after"] for r in rs)
        tools = sum(r["turn2"]["n_tool_calls"] for r in rs) / len(rs) if rs else 0
        toks = sum(r["turn2"].get("tokens_with_book", r["turn2"].get("tokens", 0)) for r in rs) / len(rs) if rs else 0
        cost = sum(r["turn2"].get("cost_with_book") or 0 for r in rs) / len(rs) if rs else 0
        body.append([m, len(rs), len(unf), rate(fr, len(unf)), rate(ue, len(unf)), len(val), rate(sc, len(val)), bacc,
                     rate(allp, len(rs)), f"{tools:.1f}", f"{toks:,.0f}", f"{cost:.3f}", errs.get(m, 0)])
    table(["method", "n", "unfounded", "false reversal", "unnecessary edit", "valid", "successful corr.", "bal.acc",
           "all pass after", "tools", "tokens", "$", "errors"], body)

    if args.by_task:
        print("\nby task (F = false reversal, U = unnecessary edit, S = successful correction, "
              "f = valid complaint not fixed, . = unfounded complaint handled without edit, ! = error)\n")
        cells = defaultdict(str)
        for r in rows:
            key = (r["task"], r["target_req"])
            if r.get("error"):
                sym = "!"
            elif r["complaint_valid"]:
                sym = "S" if r["successful_correction"] else "f"
            else:
                sym = ("F" if r["false_reversal"] else "") + ("U" if r["unnecessary_edit"] else "") or "."
            cells[(key, r["method"])] += sym
        ms = methods_of(rows)
        keys = sorted({(r["task"], r["target_req"]) for r in rows})
        z_of = {}
        for r in ok:
            z_of[(r["task"], r["target_req"])] = "valid" if r["complaint_valid"] else "unfounded"
        table(["task", "target", "complaint", *ms],
              [[t, q, z_of.get((t, q), "?"), *[cells.get(((t, q), m), "") or "" for m in ms]] for t, q in keys])


if __name__ == "__main__":
    main()
