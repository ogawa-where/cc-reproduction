#!/usr/bin/env python3
"""Collect answers: each question + the language's instruction sentence, one isolated tool-less `claude -p` call
(Claude Code's default system prompt). Resumable: questions already answered without an error are skipped.

  python run.py --model sonnet --langs en,ja,zh,es,ar,sw --workers 8 --out results/sonnet
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import threading

import cc

HERE = os.path.dirname(os.path.abspath(__file__))
_lock = threading.Lock()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--langs", default="en,ja,zh,es,ar,sw")
    ap.add_argument("--limit", type=int, default=0, help="first N questions only (smoke test)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--system-prompt", default=None, help="replace Claude Code's system prompt (default: keep it)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    jobs = []
    for lang in args.langs.split(","):
        qs = json.load(open(os.path.join(HERE, "questions", f"{lang}.json"), encoding="utf-8"))
        path = os.path.join(args.out, f"answers-{lang}.jsonl")
        done = set()
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                r = json.loads(line)
                if not r.get("error"):
                    done.add(r["id"])
        items = qs["questions"][: args.limit or None]
        jobs += [(lang, qs["suffix"], q, path) for q in items if q["id"] not in done]
    print(f"[{dt.datetime.now():%H:%M:%S}] model={args.model}: {len(jobs)} calls -> {args.out}", flush=True)

    def one(job):
        lang, suffix, q, path = job
        sep = "" if lang in ("ja", "zh") else " "
        prompt = q["text"] + sep + suffix
        data, err = cc.call(prompt, args.model, system_prompt=args.system_prompt)
        rec = {"lang": lang, "id": q["id"], "domain": q["domain"], "subtopic": q["subtopic"], "prompt": prompt,
               "model": args.model, "answer": data["result"] if data else None,
               "model_used": list((data or {}).get("modelUsage", {})), "cost_usd": (data or {}).get("total_cost_usd"),
               "error": err}
        with _lock, open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return err

    n = errs = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for err in ex.map(one, jobs):
            n += 1
            errs += bool(err)
            if n % 100 == 0:
                print(f"[{dt.datetime.now():%H:%M:%S}] {n}/{len(jobs)} done, {errs} errors", flush=True)
    print(f"[{dt.datetime.now():%H:%M:%S}] finished {n} calls, {errs} errors", flush=True)


if __name__ == "__main__":
    main()
