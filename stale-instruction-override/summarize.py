#!/usr/bin/env python3
"""Summarise runs.jsonl produced by run.py in the shape of the paper's Figures 5 and 6.

Usage: python summarize.py runs/runs.jsonl [--by-type] [--runs]
"""
from __future__ import annotations

import argparse
import collections
import json


def pct(n, d):
    return f"{100.0 * n / d:5.1f}% ({n}/{d})" if d else "   n/a"


def majority(verdicts):
    """A run follows the file or the code when more than half of its choices did (paper, Fig. 6)."""
    n = len(verdicts)
    if not n:
        return "none"
    c = collections.Counter(v["verdict"] for v in verdicts)
    if c["follow_file"] * 2 > n:
        return "file"
    if c["follow_code"] * 2 > n:
        return "code"
    return "no majority"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--by-type", action="store_true", help="also break the choices down by kind")
    ap.add_argument("--runs", action="store_true", help="also list every run")
    args = ap.parse_args()

    runs = [json.loads(ln) for ln in open(args.path, encoding="utf-8") if ln.strip()]
    valid = [r for r in runs if r.get("valid")]
    invalid = [r for r in runs if not r.get("valid")]
    conds = sorted({r["cond"] for r in valid})
    names = {"A": "A: without the sentence", "B": "B: with the sentence"}

    print(f"runs: {len(runs)} total, {len(valid)} valid, {len(invalid)} invalid")
    for r in invalid:
        print(f"  invalid {r['run']}: {r.get('failures')}")
    print()
    print("Choices (paper Fig. 5a; paper A: file 86.4% / code 7.5%, B: code 94.4% for Claude Code)")
    for c in conds:
        vs = [v for r in valid if r["cond"] == c for v in r["verdicts"]]
        cnt = collections.Counter(v["verdict"] for v in vs)
        print(f"  {names.get(c, c)}: matches file {pct(cnt['follow_file'], len(vs))}, "
              f"matches code {pct(cnt['follow_code'], len(vs))}, neither {pct(cnt['neither'], len(vs))}")
    print()
    print("Runs (paper Fig. 6; one run = majority of its choices)")
    for c in conds:
        rs = [r for r in valid if r["cond"] == c]
        maj = collections.Counter(majority(r["verdicts"]) for r in rs)
        rep = sum(1 for r in rs if (r.get("conflict") or {}).get("label") == "YES")
        unj = sum(1 for r in rs if (r.get("conflict") or {}).get("label") not in ("YES", "NO"))
        rew = sum(1 for r in rs if r.get("rewrote_existing"))
        tp = sum(1 for r in rs if (r.get("tests") or {}).get("all_pass"))
        ep = sum(1 for r in rs if (r.get("tests") or {}).get("existing_pass"))
        doc = sum(1 for r in rs if r.get("doc_edited"))
        tools = [r["tool_calls"] for r in rs if r.get("tool_calls") is not None]
        secs = [r["seconds"] for r in rs if r.get("seconds") is not None]
        print(f"  {names.get(c, c)} ({len(rs)} runs)")
        print(f"    followed the file: {maj['file']}, followed the code: {maj['code']}, "
              f"no majority: {maj['no majority']}")
        print(f"    conflict reported in final reply: {pct(rep, len(rs))}"
              + (f"  [{unj} not judged]" if unj else ""))
        print(f"    rewrote existing code (>=20 lines removed): {rew}")
        print(f"    tests pass (original + held-out): {pct(tp, len(rs))}; original tests pass: {pct(ep, len(rs))}")
        print(f"    edited CLAUDE.md: {doc}; mean tool calls: {sum(tools)/len(tools) if tools else 0:.1f}; "
              f"mean seconds: {sum(secs)/len(secs) if secs else 0:.0f}")
    if args.by_type:
        print()
        print("Choices by kind (share matching the file / the code)")
        kinds = sorted({v["type"] for r in valid for v in r["verdicts"]})
        for k in kinds:
            row = []
            for c in conds:
                vs = [v for r in valid if r["cond"] == c for v in r["verdicts"] if v["type"] == k]
                cnt = collections.Counter(v["verdict"] for v in vs)
                row.append(f"{c}: file {pct(cnt['follow_file'], len(vs))} code {pct(cnt['follow_code'], len(vs))}")
            print(f"  {k:8s} " + " | ".join(row))
    if args.runs:
        print()
        for r in runs:
            vs = ", ".join(f"{v['type']}={v['verdict']}" for v in r.get("verdicts", []))
            print(f"  {r['run']}: valid={r.get('valid')} tests={(r.get('tests') or {}).get('all_pass')} "
                  f"conflict={(r.get('conflict') or {}).get('label')} rewrote={r.get('rewrote_existing')} | {vs}")


if __name__ == "__main__":
    main()
