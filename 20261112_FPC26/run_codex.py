#!/usr/bin/env python3
"""Collect answers from Codex CLI (`codex exec`), in the same format as run.py, so judge.py and summarize.py work
unchanged. Run it on a machine where Codex is logged in (this cloud session cannot reach OpenAI).

Each question runs in an empty working directory with a fresh CODEX_HOME that holds only a copy of auth.json, so no
AGENTS.md, config.toml or rules file reaches the model. The sandbox is read-only.

  python run_codex.py --model gpt-5.5 --langs en,ja,zh,es,ar,sw --workers 4 --out results/codex-gpt-5.5
  python run_codex.py --model gpt-5.5 -c model_reasoning_effort=low --out results/codex-gpt-5.5-low
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
_lock = threading.Lock()


def ask(prompt, model, configs, auth, timeout):
    tmp = tempfile.mkdtemp(prefix="fpc26_codex_")
    cwd, home = os.path.join(tmp, "cwd"), os.path.join(tmp, "home")
    os.makedirs(cwd)
    os.makedirs(home)
    shutil.copy(auth, os.path.join(home, "auth.json"))
    out = os.path.join(tmp, "last.txt")
    cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "--ignore-user-config", "--ignore-rules",
           "-s", "read-only", "-C", cwd, "--json", "-o", out]
    if model:
        cmd += ["-m", model]
    for c in configs:
        cmd += ["-c", c]
    env = {**os.environ, "CODEX_HOME": home}
    try:
        r = subprocess.run(cmd + [prompt], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, stdin=subprocess.DEVNULL)
        answer = open(out, encoding="utf-8").read().strip() if os.path.exists(out) else ""
        used = None
        for line in r.stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            used = ev.get("model") or (ev.get("msg") or {}).get("model") or used
        if not answer:
            return None, used, f"no answer (exit {r.returncode}): {r.stderr[-300:]}"
        return answer, used, None
    except subprocess.TimeoutExpired:
        return None, None, "timeout"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="", help="codex -m value (empty: Codex's default model)")
    ap.add_argument("-c", "--config", action="append", default=[], help="extra codex -c key=value (repeatable)")
    ap.add_argument("--langs", default="en,ja,zh,es,ar,sw")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--auth", default=os.path.expanduser("~/.codex/auth.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if shutil.which("codex") is None:
        raise SystemExit("codex not found on PATH (npm install -g @openai/codex)")
    if not os.path.exists(args.auth):
        raise SystemExit(f"{args.auth} not found: run `codex login` first")
    os.makedirs(args.out, exist_ok=True)
    name = "codex:" + (args.model or "default") + "".join(f" {c}" for c in args.config)

    jobs = []
    for lang in args.langs.split(","):
        qs = json.load(open(os.path.join(HERE, "questions", f"{lang}.json"), encoding="utf-8"))
        path = os.path.join(args.out, f"answers-{lang}.jsonl")
        done = set()
        if os.path.exists(path):
            done = {json.loads(l)["id"] for l in open(path, encoding="utf-8") if not json.loads(l).get("error")}
        jobs += [(lang, qs["suffix"], q, path) for q in qs["questions"][: args.limit or None] if q["id"] not in done]
    print(f"[{dt.datetime.now():%H:%M:%S}] {name}: {len(jobs)} calls -> {args.out}", flush=True)

    def one(job):
        lang, suffix, q, path = job
        prompt = q["text"] + ("" if lang in ("ja", "zh") else " ") + suffix
        answer, used, err = ask(prompt, args.model, args.config, args.auth, args.timeout)
        rec = {"lang": lang, "id": q["id"], "domain": q["domain"], "subtopic": q["subtopic"], "prompt": prompt,
               "model": name, "answer": answer, "model_used": [used] if used else [], "cost_usd": None, "error": err}
        with _lock, open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return err

    n = errs = 0
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for err in ex.map(one, jobs):
            n += 1
            errs += bool(err)
            if n % 50 == 0 or err and errs <= 3:
                print(f"[{dt.datetime.now():%H:%M:%S}] {n}/{len(jobs)} done, {errs} errors {err or ''}", flush=True)
    print(f"[{dt.datetime.now():%H:%M:%S}] finished {n} calls, {errs} errors", flush=True)


if __name__ == "__main__":
    main()
