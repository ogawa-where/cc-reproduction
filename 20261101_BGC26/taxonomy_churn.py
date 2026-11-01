#!/usr/bin/env python3
"""Construction-time instability: theme churn between independently rebuilt TGA taxonomies
(the paper notes TGA stability is conditional on a fixed taxonomy; rebuilding moves instability to ingestion).
Usage: python taxonomy_churn.py runs/tga_store-sonnet.json runs/taxonomy_rebuilds-sonnet.jsonl"""
from __future__ import annotations

import itertools
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align import assign, key, rate  # noqa: E402
from run import clean_env  # noqa: E402


def main():
    store, rebuilds = sys.argv[1], sys.argv[2]
    taxonomies = [[t["name"] for t in json.load(open(store, encoding="utf-8"))["taxonomy"]["themes"]]]
    for l in open(rebuilds, encoding="utf-8"):
        r = json.loads(l)
        if r.get("taxonomy"):
            taxonomies.append([t["name"] for t in r["taxonomy"]["themes"]])
    cache_path = os.path.join(os.path.dirname(os.path.abspath(store)), "alignment-cache.json")
    cache = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}
    parent = tempfile.mkdtemp(prefix="taxchurn_")
    cfg = os.path.join(parent, "cfg"); os.makedirs(cfg); open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "cwd"); os.makedirs(cwd)
    env = clean_env(cfg)
    print(f"{len(taxonomies)} taxonomies, sizes {[len(t) for t in taxonomies]}")
    for g in (0.70, 0.85, 0.95):
        churn = []
        for a, b in itertools.combinations(taxonomies, 2):
            k = key(a, b)
            if k not in cache:
                cache[k] = rate(a, b, "sonnet", env, cwd) or {}
            M = len(assign(cache[k], len(a), len(b), g))
            churn.append(1 - 2 * M / (len(a) + len(b)))
        print(f"gamma={g:.2f}: mean theme churn between rebuilt taxonomies = {sum(churn) / len(churn):.3f} over {len(churn)} pairs")
    json.dump(cache, open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
    for i, t in enumerate(taxonomies):
        print(f"taxonomy {i}: " + " | ".join(t))


if __name__ == "__main__":
    main()
