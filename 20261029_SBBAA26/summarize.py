#!/usr/bin/env python3
"""Aggregate runs.jsonl from run.py: drop rate per constraint category (paper Fig. 4b) and
post-compaction behaviour. Usage: python summarize.py runs/runs.jsonl [--runs]"""
from __future__ import annotations

import argparse
import collections
import json
import math

PAPER = {  # SWE-chat sessions (produced with Claude Code), Salle et al. 2026, Section 4.2 / Appendix 6.11
    "overall": (19.0, 269), "feature_requirement": (6.2, 96), "technical_parameter": (None, 67),
    "scope_exclusion": (36.8, 38), "process_instruction": (35.9, 39), "named_source_or_tool": (None, 16),
    "structural_convention": (None, 10), "soft_preference": (None, 3)}
ORDER = ["feature_requirement", "technical_parameter", "named_source_or_tool", "structural_convention",
         "soft_preference", "process_instruction", "scope_exclusion"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * (c - h), 100 * (c + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--runs", action="store_true")
    args = ap.parse_args()
    runs = [json.loads(l) for l in open(args.path, encoding="utf-8") if l.strip()]
    valid = [r for r in runs if r.get("valid")]
    print(f"runs: {len(runs)} total, {len(valid)} valid")
    for r in runs:
        if not r.get("valid"):
            print(f"  invalid {r['run']}: {r.get('failures')}")
    cons = [c for r in valid for c in r.get("constraints", []) if c.get("verdict")]
    unjudged = sum(1 for r in valid for c in r.get("constraints", []) if not c.get("verdict"))
    drop = lambda cs: sum(1 for c in cs if c["verdict"] in ("dropped", "contradicted"))  # noqa: E731
    print()
    print("Drop rate per category (this reproduction vs. paper's SWE-chat sessions)")
    print(f"  {'category':22s} {'dropped/n':>10s} {'rate':>7s} {'95% CI':>16s}   paper")
    for cat in ORDER:
        cs = [c for c in cons if c["category"] == cat]
        k, n = drop(cs), len(cs)
        lo, hi = wilson(k, n)
        pr, pn = PAPER.get(cat, (None, None))
        paper = f"{pr:.1f}% (n={pn})" if pr is not None else f"n/a (n={pn})"
        print(f"  {cat:22s} {k:>4d}/{n:<5d} {100*k/n if n else 0:6.1f}% [{lo:5.1f}, {hi:5.1f}]   {paper}")
    k, n = drop(cons), len(cons)
    lo, hi = wilson(k, n)
    print(f"  {'overall':22s} {k:>4d}/{n:<5d} {100*k/n if n else 0:6.1f}% [{lo:5.1f}, {hi:5.1f}]   19.0% (n=269)")
    if unjudged:
        print(f"  ({unjudged} constraints without a verdict)")
    what = [c for c in cons if c["category"] in ("feature_requirement", "technical_parameter")]
    how = [c for c in cons if c["category"] in ("process_instruction", "scope_exclusion")]
    rw, rh = (drop(what) / len(what) if what else 0), (drop(how) / len(how) if how else 0)
    print()
    print(f"What to build (feature + technical): {drop(what)}/{len(what)} = {100*rw:.1f}%   "
          f"How to work / what not to do (process + scope): {drop(how)}/{len(how)} = {100*rh:.1f}%   "
          f"ratio = {rh/rw if rw else float('inf'):.1f}x (paper: ~6x)")
    if any("judge_category" in c for c in cons):
        agree = sum(1 for c in cons if c.get("judge_category") == c["category"])
        print(f"Planted category vs. paper's classifier: agreement {agree}/{len(cons)}")
    print()
    print("Compaction and behaviour after it")
    pre = [r["compact_metadata"]["pre_tokens"] for r in valid if r.get("compact_metadata")]
    print(f"  tokens before compaction: mean {sum(pre)/len(pre) if pre else 0:.0f}, min {min(pre) if pre else 0}, max {max(pre) if pre else 0}")
    cnt = collections.Counter()
    for r in valid:
        ch = r.get("checks", {})
        cnt["runs"] += 1
        cnt["untouched file modified"] += bool(ch.get("untouched_files_modified"))
        cnt["existing test removed"] += bool(ch.get("existing_tests_removed"))
        cnt["pytest run in probe turn"] += bool(ch.get("pytest_run_in_probe"))
        cnt["git commit attempted"] += bool(ch.get("git_commit_attempted"))
        cnt["new test file created"] += bool(ch.get("new_test_files"))
    for key in ("untouched file modified", "existing test removed", "pytest run in probe turn", "git commit attempted", "new test file created"):
        print(f"  {key}: {cnt[key]}/{cnt['runs']} runs")
    rounds = collections.defaultdict(lambda: [0, 0])
    for r in valid:
        for rd in r.get("rounds", []):
            for v in rd["verdicts"]:
                if v.get("verdict"):
                    rounds[rd["compaction"]][1] += 1
                    rounds[rd["compaction"]][0] += v["verdict"] in ("dropped", "contradicted")
    if len(rounds) > 1:
        print()
        print("Drop rate by compaction round (paper Q3: 0.92 of 3 rule categories dropped at the 1st compaction, 1.93 by the 10th)")
        for k in sorted(rounds):
            d, n = rounds[k]
            lo, hi = wilson(d, n)
            how_d = how_n = 0
            for r in valid:
                for rd in r.get("rounds", []):
                    if rd["compaction"] == k:
                        for v in rd["verdicts"]:
                            if v.get("verdict") and v["category"] in ("process_instruction", "scope_exclusion"):
                                how_n += 1; how_d += v["verdict"] in ("dropped", "contradicted")
            print(f"  compaction {k}: dropped {d}/{n} = {100*d/n if n else 0:.1f}% [{lo:.1f}, {hi:.1f}]; process+scope {how_d}/{how_n}")
    if args.runs:
        print()
        for r in runs:
            cs = r.get("constraints", [])
            dropped = [c["id"] + ":" + c["category"] for c in cs if c.get("verdict") in ("dropped", "contradicted")]
            print(f"  {r['run']}: valid={r.get('valid')} pre_tokens={(r.get('compact_metadata') or {}).get('pre_tokens')} "
                  f"dropped {len(dropped)}/{len(cs)} {dropped} checks={r.get('checks')}")


if __name__ == "__main__":
    main()
