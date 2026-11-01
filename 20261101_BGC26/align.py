#!/usr/bin/env python3
"""Semantic theme alignment between run pairs (paper Section 3: one-to-one assignment that first maximizes
match cardinality, then total similarity, over edges with similarity >= gamma).

The paper embeds theme names with text-embedding-3-large (cosine >= 0.82). No embedding model is available
offline here, so a Claude judge (Sonnet by default) rates the similarity of theme-name pairs in [0, 1]; the
ratings are cached per unordered pair of theme-name lists and reused across thresholds.
Usage: python align.py runs/answers-sonnet.jsonl [--judge-model sonnet] [--workers 4]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import itertools
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prompts as P  # noqa: E402
from run import claude_call, clean_env, log  # noqa: E402


def key(a_names, b_names):
    return hashlib.sha1(json.dumps([a_names, b_names], ensure_ascii=False).encode()).hexdigest()


def rate(a_names, b_names, model, env, cwd):
    user = ("List A:\n" + "\n".join(f"A{i}: {n}" for i, n in enumerate(a_names)) +
            "\n\nList B:\n" + "\n".join(f"B{j}: {n}" for j, n in enumerate(b_names)) +
            "\n\nReturn the related pairs as (a index, b index, similarity).")
    obj, meta = claude_call(model, P.MATCH_PROMPT, user, P.MATCH_SCHEMA, env, cwd, timeout=300)
    if not obj:
        return None
    sims = {}
    for p in obj.get("pairs", []):
        try:
            a, b, s = int(p["a"]), int(p["b"]), float(p["similarity"])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= a < len(a_names) and 0 <= b < len(b_names):
            sims[f"{a},{b}"] = max(0.0, min(1.0, s))
    return sims


def assign(sims, ka, kb, gamma):
    """One-to-one assignment: maximize cardinality, then total similarity, over edges >= gamma."""
    edges = [(a, b, s) for k, s in sims.items() for a, b in [map(int, k.split(","))] if s >= gamma]
    if not edges:
        return []
    by_a = {}
    for a, b, s in edges:
        by_a.setdefault(a, []).append((b, s))
    a_nodes = sorted(by_a)
    best = ([], 0, 0.0)

    def rec(i, used_b, chosen, total):
        nonlocal best
        if len(chosen) + (len(a_nodes) - i) < best[1]:
            return
        if i == len(a_nodes):
            if (len(chosen), total) > (best[1], best[2]):
                best = (list(chosen), len(chosen), total)
            return
        a = a_nodes[i]
        for b, s in sorted(by_a[a], key=lambda x: -x[1]):
            if b not in used_b:
                used_b.add(b); chosen.append((a, b, s))
                rec(i + 1, used_b, chosen, total + s)
                chosen.pop(); used_b.discard(b)
        rec(i + 1, used_b, chosen, total)

    rec(0, set(), [], 0.0)
    return best[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--judge-model", default="sonnet")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    answers = [json.loads(l) for l in open(args.path, encoding="utf-8") if l.strip()]
    cache_path = os.path.join(os.path.dirname(os.path.abspath(args.path)), "alignment-cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    parent = tempfile.mkdtemp(prefix="align_")
    cfg = os.path.join(parent, "cfg"); os.makedirs(cfg); open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "cwd"); os.makedirs(cwd)
    env = clean_env(cfg)
    cells = {}
    for a in answers:
        if a.get("valid"):
            cells.setdefault((a["model"], a["system"], a["prompt"], a["question"]), []).append(a)
    jobs = []
    for cell, runs in cells.items():
        runs.sort(key=lambda a: a["run"])
        for x, y in itertools.combinations(runs, 2):
            an = [t["name"] for t in x["answer"]["themes"]]
            bn = [t["name"] for t in y["answer"]["themes"]]
            k = key(an, bn)
            if k not in cache:
                jobs.append((k, an, bn))
    jobs = list({j[0]: j for j in jobs}.values())
    log(f"{len(cells)} cells, {sum(len(r) * (len(r) - 1) // 2 for r in cells.values())} run pairs, {len(jobs)} pairs to rate")
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(rate, an, bn, args.judge_model, env, cwd): k for k, an, bn in jobs}
        for i, f in enumerate(cf.as_completed(futs), start=1):
            sims = f.result()
            if sims is not None:
                cache[futs[f]] = sims
            if i % 20 == 0 or i == len(jobs):
                log(f"rated {i}/{len(jobs)}")
                json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"alignment cache: {len(cache)} rated pairs -> {cache_path}")


if __name__ == "__main__":
    main()
