#!/usr/bin/env python3
"""Re-run the paper's judges on the summaries already recorded in a runs.jsonl, without re-running
the sessions. Writes a new runs.jsonl (default: <input>.rejudged.jsonl).

Usage: python rejudge.py runs-2.1.128/runs.jsonl [--out FILE] [--judge-model sonnet] [--classify]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as harness  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default="")
    ap.add_argument("--judge-model", default="sonnet")
    ap.add_argument("--classify", action="store_true")
    ap.add_argument("--only-missing", action="store_true", help="judge only constraints that have no verdict yet")
    args = ap.parse_args()
    out = args.out or args.path.replace(".jsonl", ".rejudged.jsonl")
    parent = tempfile.mkdtemp(prefix="rejudge_")
    env = harness.clean_env([], {})
    records = [json.loads(l) for l in open(args.path, encoding="utf-8") if l.strip()]
    with open(out, "w", encoding="utf-8") as fh:
        for rec in records:
            cons = rec.get("constraints") or []
            summaries = rec.get("summaries") or ([rec["summary"]] if rec.get("summary") else [])
            if not cons or not summaries:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue
            if args.only_missing and all(c.get("verdict") for c in cons) and all(
                    v.get("verdict") for rd in rec.get("rounds", []) for v in rd["verdicts"]):
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue
            harness.log(f"{rec['run']}: judging {len(cons)} constraints x {len(summaries)} summaries")
            rec["rounds"] = []
            for k, text in enumerate(summaries, start=1):
                vs = harness.judge_preservation(text, cons, args.judge_model, env, parent)
                if k == 1:
                    for c in cons:
                        v = vs.get(c["id"], {})
                        c.update({"verdict": v.get("verdict"), "evidence": v.get("evidence", ""),
                                  "confidence": v.get("confidence"), "reasoning": v.get("reasoning", ""), "error": v.get("error")})
                rec["rounds"].append({"compaction": k, "verdicts": [
                    {"id": c["id"], "category": c["category"], "verdict": vs.get(c["id"], {}).get("verdict"),
                     "evidence": vs.get(c["id"], {}).get("evidence", "")} for c in cons]})
            if args.classify:
                cls = harness.judge_classification(cons, args.judge_model, env, parent)
                for c in cons:
                    c["judge_category"] = cls.get(c["id"], {}).get("category")
            rec["failures"] = [f for f in rec.get("failures", []) if f.get("stage") != "judge"]
            n_none = sum(1 for c in cons if not c.get("verdict"))
            if n_none:
                rec["failures"].append({"stage": "judge", "unjudged": n_none,
                                        "error": next((c.get("error") for c in cons if c.get("error")), "")})
            n_drop = sum(1 for c in cons if c.get("verdict") in ("dropped", "contradicted"))
            harness.log(f"{rec['run']}: dropped {n_drop}/{len(cons)} at compaction 1" + (f", {n_none} unjudged" if n_none else ""))
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    harness.log(f"wrote {out}; summarise with: python summarize.py {out}")


if __name__ == "__main__":
    main()
