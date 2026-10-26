#!/usr/bin/env python3
"""Reproduce arXiv:2610.30571 (Xu & Wu 2026), "Stale Instruction Files Override the Code in
Coding Agents: A One-Sentence Fix", with Claude Code.

For each task x condition x repetition this script
  1. copies the task's repo to a fresh workspace and writes its stale instruction file as CLAUDE.md,
  2. gives Claude Code a dedicated CLAUDE_CONFIG_DIR whose user-level CLAUDE.md is the condition
     (A: empty, B: the one sentence),
  3. runs `claude -p` with the paper's flags (Appendix A), the feature request on stdin,
  4. takes a full-context git diff of the result, classifies each convention choice with the
     paper's choice judge (follow_file / follow_code / neither), restores the original tests and
     runs them together with the held-out feature test, detects rewrites of existing code
     (>= 20 lines removed from pre-existing .py files), and asks a second model (Opus) whether
     the final reply names a documentation-vs-code conflict,
  5. appends one record per run to <out>/runs.jsonl.

Sources of tasks:
  --source paper  the 40 projects of the paper (run ./fetch_paper_data.sh first)
  --source mini   the two small self-authored projects under mini/tasks (same format)

Examples:
  python run.py --source mini --reps 1
  python run.py --source paper --tasks P01,P05,P16 --cond A,B --reps 2 --model sonnet
  python summarize.py runs/runs.jsonl
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.join(HERE, "paper-data")
SOURCES = {"paper": os.path.join(PAPER, "tasks"), "mini": os.path.join(HERE, "mini", "tasks")}
CONDITIONS = {"A": os.path.join(HERE, "conditions", "A_empty.md"),
              "B": os.path.join(HERE, "conditions", "B_fix.md")}
CRITERIA = os.path.join(HERE, "criteria", "conflict_criteria.md")
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")

# Appendix A: variables of the parent session that must not reach the tested agent.
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC|OPENAI|CODEX|AWS_|GOOGLE_|VERTEX|BEDROCK|MCP_)", re.I)
_SCRUB_EXACT = {"DISABLE_TELEMETRY", "DISABLE_PROMPT_CACHING", "DISABLE_FEEDBACK_COMMAND",
                "DISABLE_AUTOUPDATER", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME", "VIRTUAL_ENV"}

AGENT_FLAGS = [
    "--permission-mode", "acceptEdits",
    "--output-format", "stream-json", "--verbose", "--strict-mcp-config",
    "--allowedTools", "Bash(python *)", "Bash(python3 *)", "Bash(py *)", "Bash(pytest *)",
    "PowerShell(python *)", "PowerShell(python3 *)", "PowerShell(py *)", "PowerShell(pytest *)",
    "--disallowedTools", "Bash(pip *)", "Bash(python -m pip *)", "Bash(python3 -m pip *)",
    "Bash(py -m pip *)", "PowerShell(pip *)", "PowerShell(python -m pip *)",
    "PowerShell(python3 -m pip *)", "PowerShell(py -m pip *)",
]
CONFLICT_SCHEMA = json.dumps({
    "type": "object",
    "properties": {"label": {"type": "string", "enum": ["YES", "NO"]}, "evidence": {"type": "string"}},
    "required": ["label", "evidence"], "additionalProperties": False,
})


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def clean_env(keep_prefixes, extra):
    env = {}
    for k, v in os.environ.items():
        if k.upper() in _SCRUB_EXACT:
            continue
        if _SCRUB.match(k) and not any(k.upper().startswith(p.upper()) for p in keep_prefixes):
            continue
        env[k] = v
    env.update(extra)
    return env


def load_judge():
    path = os.path.join(PAPER, "scripts", "judge.py")
    if not os.path.exists(path):
        sys.exit("paper-data/scripts/judge.py not found: run ./fetch_paper_data.sh first "
                 "(the choice judge is needed for both sources)")
    spec = importlib.util.spec_from_file_location("paper_judge", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(ws, *args, check=True):
    return subprocess.run(["git", "-C", ws, "-c", "user.name=baseline", "-c", "user.email=b@x",
                           "-c", "core.autocrlf=false", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def make_workspace(task_dir, parent):
    ws = os.path.join(parent, "ws")
    shutil.copytree(os.path.join(task_dir, "repo"), ws, ignore=IGNORE)
    shutil.copyfile(os.path.join(task_dir, "instructions.md"), os.path.join(ws, "CLAUDE.md"))
    git(ws, "init", "-q")
    with open(os.path.join(ws, ".git", "info", "exclude"), "a", encoding="utf-8") as fh:
        fh.write("__pycache__/\n.pytest_cache/\n*.pyc\n")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "-m", "baseline")
    return ws


def make_config_dir(parent, cond, copy_credentials):
    cfg = os.path.join(parent, "cfg")
    os.makedirs(cfg, exist_ok=True)
    shutil.copyfile(CONDITIONS[cond], os.path.join(cfg, "CLAUDE.md"))
    if copy_credentials:
        real = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
        for name in (".credentials.json",):
            src = os.path.join(real, name)
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(cfg, name))
                os.chmod(os.path.join(cfg, name), 0o600)
    return cfg


def parse_stream(path):
    """Final reply, tool-call count, version and model from a stream-json transcript."""
    info = {"final_reply": "", "tool_calls": 0, "tool_version": None, "model": None,
            "num_turns": None, "is_error": None, "usage": None, "cost_usd": None,
            "permission_denials": 0}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = ev.get("type")
            if t == "system" and ev.get("subtype") == "init":
                info["tool_version"] = ev.get("version") or ev.get("claude_code_version")
                info["model"] = ev.get("model")
            elif t == "assistant":
                for block in ev.get("message", {}).get("content", []) or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        info["tool_calls"] += 1
            elif t == "result":
                info["final_reply"] = ev.get("result") or ""
                info["num_turns"] = ev.get("num_turns")
                info["is_error"] = ev.get("is_error")
                info["usage"] = ev.get("usage")
                info["cost_usd"] = ev.get("total_cost_usd")
                info["permission_denials"] = len(ev.get("permission_denials") or [])
    return info


def run_agent(ws, cfg, prompt, model, timeout, env, stream_path):
    cmd = ["claude", "-p", "--model", model, *AGENT_FLAGS]
    t0 = time.monotonic()
    with open(stream_path, "w", encoding="utf-8") as out:
        try:
            r = subprocess.run(cmd, cwd=ws, env=env, input=prompt, stdout=out, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout)
            code, err = r.returncode, r.stderr
        except subprocess.TimeoutExpired as exc:
            code, err = "timeout", (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    return code, err, round(time.monotonic() - t0, 1)


def full_diff(ws):
    git(ws, "add", "-A")
    r = git(ws, "diff", "--cached", "--no-renames", "--unified=100000", "HEAD")
    return r.stdout


def rewrite_stats(judge, diff_text):
    """Lines removed from pre-existing .py files, and whether CLAUDE.md was edited."""
    removed = 0
    doc_edited = False
    for f in judge.parse_diff(diff_text):
        if f.path == "CLAUDE.md":
            doc_edited = True
        if f.path.endswith(".py") and not f.is_new:
            removed += sum(1 for ln in f.removed if ln.strip())
    return removed, doc_edited


def score(judge, task_dir, task_id, ws, env):
    """Paper's score.py: original tests restored + held-out feature test, one pytest run."""
    repo = os.path.join(task_dir, "repo")
    tmp = tempfile.mkdtemp(prefix="score_")
    copy = os.path.join(tmp, "w")
    try:
        shutil.copytree(ws, copy, ignore=IGNORE)
        tests = []
        for dirpath, dirs, names in os.walk(repo):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache", ".git")]
            for fn in names:
                rel = os.path.relpath(os.path.join(dirpath, fn), repo).replace("\\", "/")
                if judge.is_test_path(rel):
                    tests.append(rel)
        tests.sort()
        for rel in tests + [c for c in ("pytest.ini",) if os.path.exists(os.path.join(repo, c))]:
            dst = os.path.join(copy, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(repo, rel), dst)
        held = f"test_heldout_{task_id}.py"
        os.makedirs(os.path.join(copy, "heldout_tests"), exist_ok=True)
        shutil.copyfile(os.path.join(task_dir, "heldout", held), os.path.join(copy, "heldout_tests", held))
        modules = [t for t in tests if t.rsplit("/", 1)[-1] not in ("conftest.py", "__init__.py")]
        xml = os.path.join(tmp, "junit.xml")
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "junit_family=xunit2",
               "--junitxml", xml, *modules, "heldout_tests/" + held]
        penv = dict(env, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        try:
            r = subprocess.run(cmd, cwd=copy, env=penv, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=600)
            code, out = r.returncode, r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            code, out = "timeout", "timeout after 600s"
        groups = {"existing": [0, 0], "feature": [0, 0]}
        if os.path.exists(xml):
            for tc in ET.parse(xml).getroot().iter("testcase"):
                g = "feature" if tc.get("classname", "").startswith("heldout_tests") else "existing"
                if tc.find("skipped") is not None:
                    continue
                groups[g][0] += 1
                if tc.find("failure") is not None or tc.find("error") is not None:
                    groups[g][1] += 1
        ex_ok = groups["existing"][0] > 0 and groups["existing"][1] == 0
        fe_ok = groups["feature"][0] > 0 and groups["feature"][1] == 0
        return {"existing_pass": ex_ok, "feature_pass": fe_ok, "all_pass": code == 0 and ex_ok and fe_ok,
                "pytest_exit": code, "existing_ran": groups["existing"][0],
                "existing_failed": groups["existing"][1], "feature_ran": groups["feature"][0],
                "feature_failed": groups["feature"][1], "pytest_tail": out[-3000:]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge_conflict(reply, judge_model, env, parent):
    """Blind judge of the final reply (paper: Opus, no tools, instruction files off)."""
    if not reply.strip():
        return {"label": None, "evidence": "", "error": "empty reply"}
    cfg = os.path.join(parent, "judge_cfg")
    os.makedirs(cfg, exist_ok=True)
    open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    with open(CRITERIA, encoding="utf-8") as fh:
        criteria = fh.read()
    cmd = ["claude", "-p", "--model", judge_model, "--safe-mode", "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "json", "--json-schema", CONFLICT_SCHEMA,
           "--system-prompt", criteria]
    jenv = dict(env, CLAUDE_CONFIG_DIR=cfg)
    empty = os.path.join(parent, "judge_cwd")
    os.makedirs(empty, exist_ok=True)
    last_err = ""
    for _ in range(3):
        try:
            r = subprocess.run(cmd, cwd=empty, env=jenv, input="Reply to judge:\n\n" + reply,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        except subprocess.TimeoutExpired:
            last_err = "timeout"
            continue
        try:
            data = json.loads(r.stdout)
            obj = data.get("structured_output") or json.loads(data.get("result") or "{}")
            if obj.get("label") in ("YES", "NO"):
                return {"label": obj["label"], "evidence": obj.get("evidence", "")}
            last_err = f"unexpected output: {r.stdout[-300:]}"
        except (json.JSONDecodeError, AttributeError):
            last_err = f"exit {r.returncode}: {(r.stderr or r.stdout)[-300:]}"
    return {"label": None, "evidence": "", "error": last_err}


def one_run(args, judge, source, task_id, cond, rep, out_dir, keep_prefixes, attempt=1):
    task_dir = os.path.join(SOURCES[source], task_id)
    with open(os.path.join(task_dir, "task.json"), encoding="utf-8") as fh:
        task = json.load(fh)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{task_id}-{cond}-r{rep}-{stamp}" + (f"-retry{attempt - 1}" if attempt > 1 else "")
    art = os.path.join(out_dir, run_id)
    os.makedirs(art, exist_ok=True)
    parent = tempfile.mkdtemp(prefix=f"stale_{run_id}_")   # outside any repo: no ancestor CLAUDE.md
    rec = {"run": run_id, "source": source, "repo": task_id, "agent": "claude", "cond": cond, "rep": rep,
           "n_decisions": len(task["decisions"]), "valid": True, "failures": [], "attempt": attempt,
           "started": dt.datetime.now().isoformat(timespec="seconds")}
    try:
        ws = make_workspace(task_dir, parent)
        cfg = make_config_dir(parent, cond, args.copy_credentials)
        env = clean_env(keep_prefixes, {
            "CLAUDE_CONFIG_DIR": cfg, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
            "DISABLE_AUTOUPDATER": "1", "PYTHONIOENCODING": "utf-8",
        })
        log(f"{run_id}: start (model={args.model}, cond={cond})")
        stream = os.path.join(art, "stream.jsonl")
        code, err, seconds = run_agent(ws, cfg, task["prompt"], args.model, args.timeout, env, stream)
        info = parse_stream(stream)
        rec.update({"exit_code": code, "seconds": seconds, "tool_calls": info["tool_calls"],
                    "permission_denials": info["permission_denials"],
                    "tool_version": info["tool_version"], "model": info["model"],
                    "num_turns": info["num_turns"], "usage": info["usage"], "cost_usd": info["cost_usd"],
                    "final_reply": info["final_reply"]})
        if err.strip():
            with open(os.path.join(art, "stderr.txt"), "w", encoding="utf-8") as fh:
                fh.write(err)
        if code != 0 or info["is_error"] or not info["final_reply"]:
            rec["valid"] = False
            rec["failures"].append({"stage": "agent", "exit": code, "is_error": info["is_error"],
                                    "stderr_tail": err[-500:]})
        diff = full_diff(ws)
        with open(os.path.join(art, "diff.patch"), "w", encoding="utf-8") as fh:
            fh.write(diff)
        with open(os.path.join(art, "final_reply.md"), "w", encoding="utf-8") as fh:
            fh.write(info["final_reply"])
        rec["diff"] = diff
        py_changed = [f.path for f in judge.parse_diff(diff) if f.path.endswith(".py")]
        if not py_changed and info["permission_denials"]:
            rec["valid"] = False
            rec["failures"].append({"stage": "agent", "reason": "blocked",
                                    "detail": f"{info['permission_denials']} permission denial(s) and no .py file changed"})
        rec["verdicts"] = judge.judge(task, diff)
        removed, doc_edited = rewrite_stats(judge, diff)
        rec["removed_existing_lines"] = removed
        rec["rewrote_existing"] = removed >= 20
        rec["doc_edited"] = doc_edited
        rec["tests"] = score(judge, task_dir, task_id, ws, env)
        if args.conflict_judge:
            rec["conflict"] = judge_conflict(info["final_reply"], args.judge_model, env, parent)
        else:
            rec["conflict"] = {"label": None, "evidence": "", "error": "judge disabled"}
        summary = ", ".join(f"{v['type']}={v['verdict']}" for v in rec["verdicts"])
        log(f"{run_id}: done in {seconds}s, {rec['tool_calls']} tool calls, tests all_pass="
            f"{rec['tests']['all_pass']}, conflict={rec['conflict']['label']}, {summary}")
    except Exception as exc:  # noqa: BLE001
        rec["valid"] = False
        rec["failures"].append({"stage": "harness", "error": repr(exc)})
        log(f"{run_id}: harness error {exc!r}")
    finally:
        if args.keep_workspaces:
            shutil.move(parent, os.path.join(art, "workspace"))
        else:
            shutil.rmtree(parent, ignore_errors=True)
    with open(os.path.join(art, "record.json"), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "runs.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=sorted(SOURCES), default="mini")
    ap.add_argument("--tasks", default="", help="comma-separated task ids (default: all of the source)")
    ap.add_argument("--cond", default="A,B", help="conditions to run: A (empty), B (the sentence)")
    ap.add_argument("--reps", type=int, default=1, help="repetitions per task and condition (paper: 2)")
    ap.add_argument("--model", default="sonnet", help="model for the tested agent (paper: sonnet)")
    ap.add_argument("--judge-model", default="opus", help="model for the blind conflict judge (paper: opus)")
    ap.add_argument("--no-conflict-judge", dest="conflict_judge", action="store_false")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per agent run (paper: 1800)")
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--copy-credentials", action="store_true",
                    help="copy .credentials.json from the real config dir into the per-run config dir "
                         "(needed on Linux/Windows when you are logged in via the config dir)")
    ap.add_argument("--keep-env", default="",
                    help="comma-separated env-var prefixes to keep although Appendix A scrubs them, "
                         "e.g. ANTHROPIC when auth is via ANTHROPIC_API_KEY / ANTHROPIC_BASE_URL")
    ap.add_argument("--keep-workspaces", action="store_true", help="keep each run's workspace under --out")
    ap.add_argument("--selftest", action="store_true",
                    help="only run the choice judge's self-test on the selected tasks")
    args = ap.parse_args()

    judge = load_judge()
    tasks_root = SOURCES[args.source]
    if not os.path.isdir(tasks_root):
        sys.exit(f"no tasks at {tasks_root}" + (" (run ./fetch_paper_data.sh)" if args.source == "paper" else ""))
    task_ids = [t for t in args.tasks.split(",") if t] or sorted(
        d for d in os.listdir(tasks_root) if os.path.isfile(os.path.join(tasks_root, d, "task.json")))
    if args.selftest:
        ok = all([judge.selftest(os.path.join(tasks_root, t)) for t in task_ids])
        sys.exit(0 if ok else 1)
    conds = [c for c in args.cond.split(",") if c]
    for c in conds:
        if c not in CONDITIONS:
            sys.exit(f"unknown condition {c!r}")
    keep_prefixes = [p for p in args.keep_env.split(",") if p]
    if shutil.which("claude") is None:
        sys.exit("claude CLI not found on PATH")
    os.makedirs(args.out, exist_ok=True)
    log(f"{len(task_ids)} task(s) x {conds} x {args.reps} rep(s) -> {args.out}/runs.jsonl")
    for rep in range(1, args.reps + 1):
        for task_id in task_ids:
            for cond in conds:
                rec = one_run(args, judge, args.source, task_id, cond, rep, args.out, keep_prefixes)
                if not rec["valid"] and any(f.get("stage") == "agent" for f in rec["failures"]):
                    # Appendix A: after a timeout, a crash or a command rejected by the sandbox,
                    # the run is repeated once from a fresh copy; a second failure makes it invalid.
                    log(f"{rec['run']}: invalid ({rec['failures'][-1]}); repeating once from a fresh copy")
                    one_run(args, judge, args.source, task_id, cond, rep, args.out, keep_prefixes, attempt=2)
    log("all runs finished; summarise with: python summarize.py " + os.path.join(args.out, "runs.jsonl"))


if __name__ == "__main__":
    main()
