#!/usr/bin/env python3
"""Reproduce arXiv:2610.08036 (Bagal, Ganta & Chellingi 2026, "Same Feedback, Different Answer") with Claude Code.

Experiment cells fix a system, a prompt, a corpus and a question; n independent runs are requested per cell.
Systems (paper Section 4):
  raw          one `claude -p` call that receives every record plus the question and schema
  hierarchy    taxonomy-free: 10 ordered batches -> 10 worker calls -> 1 synthesis call (11 stochastic calls per run)
  tga          taxonomy-grounded: a taxonomy and record-level predictions are built once and stored; each run answers
               the question from the store (theme names, counts, representative IDs) without seeing raw records
Every answer uses the same strict schema (name, volume, summary, up to five evidence IDs) enforced with --json-schema.
Outputs: <out>/answers.jsonl (one line per run) plus <out>/tga_store.json.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import corpus as corpus_mod  # noqa: E402
import prompts as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC|OPENAI|CODEX|AWS_|GOOGLE_|VERTEX|BEDROCK|MCP_)", re.I)


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def clean_env(cfg):
    env = {k: v for k, v in os.environ.items() if not _SCRUB.match(k)}
    env.update({"CLAUDE_CONFIG_DIR": cfg, "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})
    return env


def claude_call(model, system_prompt, user_text, schema, env, cwd, timeout=900):
    cmd = ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config", "--no-session-persistence",
           "--output-format", "json", "--json-schema", json.dumps(schema), "--system-prompt", system_prompt]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=user_text, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, {"error": "timeout", "seconds": round(time.time() - t0, 1)}
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, {"error": f"no json: {r.stdout[-200:]} {r.stderr[-200:]}", "seconds": round(time.time() - t0, 1)}
    obj = data.get("structured_output")
    if obj is None:
        try:
            obj = json.loads(data.get("result") or "")
        except json.JSONDecodeError:
            obj = None
    meta = {"usage": data.get("usage"), "cost_usd": data.get("total_cost_usd"), "is_error": data.get("is_error"),
            "seconds": round(time.time() - t0, 1), "error": None if obj is not None else f"invalid output: {(data.get('result') or '')[:200]}"}
    return obj, meta


def format_records(records):
    return "\n".join(f"{r['alias']}\t{r.get('timestamp', '')}\t{r['text']}" for r in records)


def normalize_answer(obj, valid_ids):
    """The paper's evidence normalizer: first-seen order, in-scope aliases only, no duplicates, at most five IDs
    and never more than the reported volume. Returns (answer, valid)."""
    if not isinstance(obj, dict) or not isinstance(obj.get("themes"), list):
        return None, False
    themes = []
    for t in obj["themes"]:
        if not isinstance(t, dict) or not all(k in t for k in ("name", "volume", "summary", "evidence_ids")):
            return None, False
        seen, ids = set(), []
        for x in t["evidence_ids"] or []:
            x = str(x).strip()
            if x in valid_ids and x not in seen:
                seen.add(x)
                ids.append(x)
        try:
            vol = int(t["volume"])
        except (TypeError, ValueError):
            return None, False
        ids = ids[:min(5, max(vol, 0))]
        themes.append({"name": str(t["name"]).strip(), "volume": max(vol, 0), "summary": str(t["summary"]), "evidence_ids": ids})
    if not themes:
        return None, False
    return {"themes": themes}, True


# ---------------------------------------------------------------- systems

def run_raw(args, records, question, system_prompt, env, cwd):
    user = (f"Question: {P.QUESTIONS[question]}\n\nFeedback records (ID<TAB>text), frozen window, {len(records)} records:\n"
            + format_records(records))
    obj, meta = claude_call(args.model, system_prompt, user, P.ANSWER_SCHEMA, env, cwd)
    meta["calls"] = 1
    return obj, meta


def run_hierarchy(args, records, question, system_prompt, env, cwd):
    nb = args.batches
    size = (len(records) + nb - 1) // nb
    batches = [records[i * size:(i + 1) * size] for i in range(nb)]
    worker_out, metas = [], []
    with cf.ThreadPoolExecutor(max_workers=min(nb, args.workers)) as ex:
        futs = []
        for k, b in enumerate(batches):
            user = (f"Question: {P.QUESTIONS[question]}\n\nYou see batch {k + 1} of {nb} of the feedback records "
                    f"(ID<TAB>text), {len(b)} records:\n" + format_records(b))
            futs.append(ex.submit(claude_call, args.model, system_prompt, user, P.ANSWER_SCHEMA, env, cwd))
        for f in futs:
            obj, meta = f.result()
            worker_out.append(obj)
            metas.append(meta)
    if any(o is None for o in worker_out):
        return None, {"error": "worker failure", "calls": nb, "worker_metas": metas}
    user = (f"Question: {P.QUESTIONS[question]}\n\nThe records were analyzed in {nb} ordered batches by independent workers. "
            "Below are their structured outputs. Synthesize one final answer to the question over the whole corpus: merge "
            "equivalent themes, add up their volumes, and keep only in-scope record IDs.\n\n"
            + "\n".join(f"Worker {k + 1}: {json.dumps(o, ensure_ascii=False)}" for k, o in enumerate(worker_out)))
    obj, meta = claude_call(args.model, system_prompt, user, P.ANSWER_SCHEMA, env, cwd)
    meta["calls"] = nb + 1
    meta["worker_cost_usd"] = sum((m.get("cost_usd") or 0) for m in metas)
    return obj, meta


def build_store(args, records, env, cwd, store_path):
    """TGA ingestion: build the taxonomy once, classify every record once, persist both."""
    if os.path.exists(store_path):
        return json.load(open(store_path, encoding="utf-8"))
    log("TGA ingestion: building taxonomy")
    user = f"Feedback records (ID<TAB>text), {len(records)} records:\n" + format_records(records)
    tax, meta = claude_call(args.model, P.TAXONOMY_PROMPT, user, P.TAXONOMY_SCHEMA, env, cwd)
    if not tax:
        raise RuntimeError(f"taxonomy build failed: {meta}")
    ids = {t["id"] for t in tax["themes"]}
    log(f"TGA ingestion: {len(ids)} themes; classifying records in batches of {args.classify_batch}")
    preds = {}
    tax_text = "\n".join(f"{t['id']}: {t['name']} - {t['definition']} (subthemes: {', '.join(t['subthemes'])})" for t in tax["themes"])
    batches = [records[i:i + args.classify_batch] for i in range(0, len(records), args.classify_batch)]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(claude_call, args.model, P.CLASSIFY_PROMPT,
                          f"Taxonomy:\n{tax_text}\n\nRecords (ID<TAB>text):\n{format_records(b)}", P.CLASSIFY_SCHEMA, env, cwd)
                for b in batches]
        for f in futs:
            obj, m = f.result()
            if not obj:
                raise RuntimeError(f"classification failed: {m}")
            for p in obj["predictions"]:
                preds[str(p["record_id"])] = [t for t in p.get("theme_ids", []) if t in ids]
    store = {"taxonomy": tax, "predictions": preds, "built": dt.datetime.now().isoformat(timespec="seconds"),
             "model": args.model, "n_records": len(records)}
    json.dump(store, open(store_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return store


def store_view(store, records):
    by_theme = {t["id"]: [] for t in store["taxonomy"]["themes"]}
    for r in records:
        for tid in store["predictions"].get(r["alias"], []):
            if tid in by_theme:
                by_theme[tid].append(r["alias"])
    lines = []
    for t in store["taxonomy"]["themes"]:
        ids = by_theme[t["id"]]
        lines.append(f"- {t['name']} [{t['id']}]: {t['definition']} | subthemes: {', '.join(t['subthemes'])} | "
                     f"records: {len(ids)} | representative IDs: {', '.join(ids[:5]) if ids else '(none)'}")
    return "\n".join(lines)


def run_tga(args, records, question, store, env, cwd):
    user = (f"Question: {P.QUESTIONS[question]}\n\nTaxonomy store for the frozen window ({len(records)} records):\n"
            + store_view(store, records))
    obj, meta = claude_call(args.model, P.TGA_ANSWER_PROMPT, user, P.ANSWER_SCHEMA, env, cwd)
    meta["calls"] = 1
    return obj, meta


# ---------------------------------------------------------------- driver

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--corpus", default=os.path.join(HERE, "corpus", "feedback-300.json"),
                    help="frozen corpus JSON from make_corpus.py ('' to use the templated synthetic corpus)")
    ap.add_argument("--n-records", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--runs", type=int, default=10, help="independent runs per cell (paper: 10)")
    ap.add_argument("--systems", default="raw:consistency_first,raw:minimal,hierarchy:consistency_first,tga",
                    help="comma-separated system[:prompt] cells")
    ap.add_argument("--questions", default="reasons,pain_points,feature_requests")
    ap.add_argument("--batches", type=int, default=10, help="hierarchy: number of fixed batches (paper: 10)")
    ap.add_argument("--classify-batch", type=int, default=30)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--taxonomy-rebuilds", type=int, default=0,
                    help="additionally rebuild the TGA taxonomy this many times (construction-time instability)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    if args.corpus:
        data = json.load(open(args.corpus, encoding="utf-8"))
        records = data["records"][:args.n_records]
    else:
        records = corpus_mod.generate(args.n_records, args.seed)
        for r in records:
            r["alias"] = f"R{r['id']:04d}"
    valid_ids = {r["alias"] for r in records}
    json.dump([{k: v for k, v in r.items()} for r in records], open(os.path.join(args.out, "corpus.json"), "w"), ensure_ascii=False, indent=0)
    parent = tempfile.mkdtemp(prefix="sfda_")
    cfg = os.path.join(parent, "cfg")
    os.makedirs(cfg)
    open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "cwd")
    os.makedirs(cwd)
    env = clean_env(cfg)
    answers_path = os.path.join(args.out, f"answers-{args.model}.jsonl")
    done = set()
    if os.path.exists(answers_path):
        for line in open(answers_path, encoding="utf-8"):
            try:
                a = json.loads(line)
                done.add((a["system"], a["prompt"], a["question"], a["run"]))
            except json.JSONDecodeError:
                pass
    cells = []
    for spec in [s for s in args.systems.split(",") if s]:
        system, _, prompt = spec.partition(":")
        if system in ("raw", "hierarchy") and not prompt:
            prompt = "consistency_first"
        if system == "tga":
            prompt = "production"
        cells.append((system, prompt))
    questions = [q for q in args.questions.split(",") if q]
    store = None
    if any(s == "tga" for s, _ in cells):
        store = build_store(args, records, env, cwd, os.path.join(args.out, f"tga_store-{args.model}.json"))
    jobs = [(s, p, q, k) for s, p in cells for q in questions for k in range(1, args.runs + 1) if (s, p, q, k) not in done]
    log(f"model={args.model}, {len(records)} records, {len(cells)} systems x {len(questions)} questions x {args.runs} runs: {len(jobs)} to run")

    def one(job):
        s, p, q, k = job
        if s == "raw":
            obj, meta = run_raw(args, records, q, P.SYSTEM_PROMPTS[p], env, cwd)
        elif s == "hierarchy":
            obj, meta = run_hierarchy(args, records, q, P.SYSTEM_PROMPTS[p], env, cwd)
        else:
            obj, meta = run_tga(args, records, q, store, env, cwd)
        ans, valid = normalize_answer(obj, valid_ids)
        return {"model": args.model, "system": s, "prompt": p, "question": q, "run": k, "valid": valid,
                "answer": ans, "raw_output": obj if not valid else None, "meta": meta, "n_records": len(records)}

    # raw/tga cells are single calls: run them concurrently; hierarchy runs already fan out their workers
    with open(answers_path, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(one, j): j for j in jobs}
        for i, f in enumerate(cf.as_completed(futs), start=1):
            rec = f.result()
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            nt = len(rec["answer"]["themes"]) if rec["valid"] else 0
            log(f"{i}/{len(jobs)} {rec['system']}:{rec['prompt']} {rec['question']} run{rec['run']}: valid={rec['valid']} themes={nt} "
                f"{'' if rec['valid'] else rec['meta'].get('error')}")
    if args.taxonomy_rebuilds and store is not None:
        rebuilds_path = os.path.join(args.out, f"taxonomy_rebuilds-{args.model}.jsonl")
        user = f"Feedback records (ID<TAB>text), {len(records)} records:\n" + format_records(records)
        with open(rebuilds_path, "a", encoding="utf-8") as fh:
            for k in range(args.taxonomy_rebuilds):
                tax, meta = claude_call(args.model, P.TAXONOMY_PROMPT, user, P.TAXONOMY_SCHEMA, env, cwd)
                fh.write(json.dumps({"rebuild": k + 1, "taxonomy": tax, "meta": meta}, ensure_ascii=False) + "\n")
                log(f"taxonomy rebuild {k + 1}: {len(tax['themes']) if tax else 'invalid'} themes")
    log(f"finished -> {answers_path}; next: python align.py {answers_path} && python summarize.py {answers_path}")


if __name__ == "__main__":
    main()
