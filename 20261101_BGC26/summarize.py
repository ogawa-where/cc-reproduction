#!/usr/bin/env python3
"""Pairwise stability metrics (paper Section 3) per cell: theme churn, rank instability, birth/death,
volume disagreement, evidence churn; mean over all valid run pairs, with a threshold sweep.
Usage: python summarize.py runs/answers-sonnet.jsonl [--gamma 0.85] [--sweep]"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align import assign, key  # noqa: E402

PAPER = {("raw", "consistency_first"): "raw Opus 4.8 1,000 rec: churn 0.765, vol 0.244, rank 0.105",
         ("hierarchy", "consistency_first"): "taxonomy-free: churn 0.841, vol 0.247",
         ("tga", "production"): "TGA: churn 0.104, vol 0.000, rank 0.008"}


def kendall_tau_b(x, y):
    n = len(x)
    if n < 2:
        return None
    c = d = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif dx * dy > 0:
                c += 1
            else:
                d += 1
    den = ((c + d + tx) * (c + d + ty)) ** 0.5
    return (c - d) / den if den else None


def pair_metrics(ra, rb, sims, gamma):
    ta, tb = ra["themes"], rb["themes"]
    ka, kb = len(ta), len(tb)
    m = assign(sims, ka, kb, gamma)
    M = len(m)
    out = {"theme": 1 - 2 * M / (ka + kb), "bd": 0.5 * ((ka - M) / ka + (kb - M) / kb)}
    if M:
        out["vol"] = sum(abs(ta[a]["volume"] - tb[b]["volume"]) / max(ta[a]["volume"], tb[b]["volume"], 1) for a, b, _ in m) / M
        ev = []
        for a, b, _ in m:
            ua, ub = set(ta[a]["evidence_ids"]), set(tb[b]["evidence_ids"])
            ev.append(1 - len(ua & ub) / len(ua | ub) if (ua | ub) else 0.0)
        out["ev"] = sum(ev) / M
    if M >= 2:
        tau = kendall_tau_b([a for a, _, _ in m], [b for _, b, _ in m])
        if tau is not None:
            out["rank"] = (1 - tau) / 2
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def fmt(v, cov=None, n=None):
    if v is None:
        return "   n/a"
    s = f"{v:6.3f}"
    return s + (f" ({cov}/{n})" if cov is not None and cov != n else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--gamma", type=float, default=0.85, help="primary alignment threshold on judged similarity")
    ap.add_argument("--sweep", action="store_true", help="also report theme churn at 0.7 / 0.85 / 0.95")
    args = ap.parse_args()
    answers = [json.loads(l) for l in open(args.path, encoding="utf-8") if l.strip()]
    cache_path = os.path.join(os.path.dirname(os.path.abspath(args.path)), "alignment-cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    cells = {}
    for a in answers:
        cells.setdefault((a["model"], a["system"], a["prompt"], a["question"]), []).append(a)
    print(f"{len(answers)} answers; alignment cache {len(cache)} pairs; gamma={args.gamma}")
    print(f"{'model':7s} {'system':10s} {'prompt':18s} {'question':16s} {'valid':>6s} {'pairs':>5s} {'churn':>7s} {'rank':>14s} {'b/d':>7s} {'volume':>14s} {'evid':>7s} {'cost$':>7s}")
    macro = {}
    for cell, runs in sorted(cells.items()):
        model, system, prompt, q = cell
        valid = [r for r in runs if r.get("valid")]
        valid.sort(key=lambda r: r["run"])
        acc = {"theme": [], "rank": [], "bd": [], "vol": [], "ev": []}
        pairs = 0
        missing = 0
        for x, y in itertools.combinations(valid, 2):
            k = key([t["name"] for t in x["answer"]["themes"]], [t["name"] for t in y["answer"]["themes"]])
            if k not in cache:
                missing += 1
                continue
            pairs += 1
            pm = pair_metrics(x["answer"], y["answer"], cache[k], args.gamma)
            for kk, v in pm.items():
                acc[kk].append(v)
        cost = sum(((r["meta"] or {}).get("cost_usd") or 0) + ((r["meta"] or {}).get("worker_cost_usd") or 0) for r in runs)
        print(f"{model:7s} {system:10s} {prompt:18s} {q:16s} {len(valid):>3d}/{len(runs):<2d} {pairs:>5d} {fmt(mean(acc['theme'])):>7s} "
              f"{fmt(mean(acc['rank']), len(acc['rank']), pairs):>14s} {fmt(mean(acc['bd'])):>7s} {fmt(mean(acc['vol']), len(acc['vol']), pairs):>14s} "
              f"{fmt(mean(acc['ev'])):>7s} {cost:7.2f}" + (f"  [{missing} pairs unrated]" if missing else ""))
        macro.setdefault((model, system, prompt), []).append({k: mean(v) for k, v in acc.items()})
    print()
    print("Macro (unweighted mean over questions)            churn   rank    b/d   volume   evid   paper (Opus 4.8, 1,000 records)")
    for (model, system, prompt), qs in sorted(macro.items()):
        def mm(k):
            vals = [q[k] for q in qs if q[k] is not None]
            return mean(vals)
        print(f"  {model:7s} {system:10s} {prompt:18s}  {fmt(mm('theme'))} {fmt(mm('rank'))} {fmt(mm('bd'))} {fmt(mm('vol'))} {fmt(mm('ev'))}   {PAPER.get((system, prompt), '')}")
    if args.sweep:
        print()
        print("Theme churn by alignment threshold (macro):   gamma=0.70  0.85  0.95")
        for (model, system, prompt), _ in sorted(macro.items()):
            vals = []
            for g in (0.70, 0.85, 0.95):
                per_q = []
                for cell, runs in cells.items():
                    if cell[:3] != (model, system, prompt):
                        continue
                    valid = sorted([r for r in runs if r.get("valid")], key=lambda r: r["run"])
                    ch = []
                    for x, y in itertools.combinations(valid, 2):
                        k = key([t["name"] for t in x["answer"]["themes"]], [t["name"] for t in y["answer"]["themes"]])
                        if k in cache:
                            ch.append(pair_metrics(x["answer"], y["answer"], cache[k], g)["theme"])
                    if ch:
                        per_q.append(mean(ch))
                vals.append(mean(per_q))
            print(f"  {model:7s} {system:10s} {prompt:18s}  " + "  ".join(fmt(v) for v in vals))


if __name__ == "__main__":
    main()
