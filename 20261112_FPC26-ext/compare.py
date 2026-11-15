#!/usr/bin/env python3
"""Compare models on the English questions: how often each picks Japan.

  python compare.py results/fable results/opus ... ../20261112_FPC26/results/sonnet
"""
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "20261112_FPC26"))
from summarize import OWN, load, stats  # noqa: E402

LABELS = {"fable": "Fable 5.1", "opus": "Opus 5.5", "sonnet": "Sonnet 5.5", "haiku": "Haiku 5.5",
          "claude-sonnet-5": "Sonnet 5", "claude-opus-4-7": "Opus 4.7", "claude-opus-4-6": "Opus 4.6",
          "claude-opus-4-5": "Opus 4.5", "claude-sonnet-4-6": "Sonnet 4.6", "claude-sonnet-4-5": "Sonnet 4.5",
          "claude-haiku-4-5": "Haiku 4.5"}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def served(d):
    c = collections.Counter()
    for line in open(os.path.join(d, "answers-en.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if not r.get("error"):
            c.update(r["model_used"])
    return c


rows = []
for d in sys.argv[1:]:
    rs = load(d, "en")
    if not rs:
        continue
    s = stats(rs, "en")
    n = s["n"]
    jp_prim = s["prim"]["JP"]
    exo_total = sum(s["exo"].values())
    second = [(c, v) for c, v in s["exo"].most_common() if c != "JP"][0]
    lo, hi = wilson(jp_prim, n)
    name = os.path.basename(os.path.normpath(d))
    rows.append((jp_prim / n, LABELS.get(name, name), n, jp_prim, lo, hi, s["exo"]["JP"], exo_total, second, s,
                 served(d)))

print("| モデル | n | 日本を主に選んだ回答 | 95% 区間 | own 以外の参照に占める日本 | own 以外の 2 位 | 日本 / 2 位 | NA | diversity | entropy |")
print("|---|---|---|---|---|---|---|---|---|---|")
for rate, label, n, k, lo, hi, jp, exo, (c2, v2), s, _ in sorted(rows, key=lambda r: -r[0]):
    print(f"| {label} | {n} | {k} ({rate:.0%}) | {lo:.0%}–{hi:.0%} | {jp}/{exo} ({jp / exo:.0%}) | {c2} {v2} | "
          f"{jp / v2:.1f} | {s['na']} | {s['div']} | {s['ent']:.2f} |")
print()
for r in rows:
    print(f"{r[1]}: served {dict(r[10])}")
