#!/usr/bin/env python3
"""B26 (Bui 2026, arXiv:2610.34654, Sections 4.4-4.5): how Claude Code reacts to a user's critique in a
multi-turn coding session, with the critique's validity decided afterwards by hidden tests (see DESIGN.md).

One trial = (task, target requirement, method):
  1. copy tasks/<id>/repo to a temp dir, `git init` + baseline commit; a dedicated CLAUDE_CONFIG_DIR with an
     empty user CLAUDE.md;
  2. Turn 1: `claude -p --session-id <uuid> --input-format stream-json ...` (acceptEdits, Read/Write/Edit/Glob/Grep
     + Bash limited to python/pytest) gets spec.md; wait for the result event, close stdin;
  3. hidden tests per requirement -> z_i; visible tests once; snapshot as commit `turn1` (shared by all methods);
  4. per method: `git reset --hard turn1 && git clean -fd`, then Turn 2 in a fork of the Turn 1 session
     (`--resume <id> --fork-session`; with --no-fork a fresh session whose first message carries a transcript of
     Turn 1). The message is the complaint, plus the method's private note:
        standard      complaint only
        rule_only     + prompts.RULE_ONLY_NOTE
        verify        + prompts.VERIFY_THEN_RESPOND_NOTE
        tib           + prompts.ADJUDICATION_NOTE with a Claim Book written before the complaint is shown
                        (separate tool-less `claude -p --json-schema` call on a record of the session)
        record_after  as tib, but the Claim Book call also sees the complaint
  5. hidden tests again -> r_i; visible tests; edited_source; tool calls; usage; seconds;
  6. one JSON line per trial in <out>/trials-<model>.jsonl (Turn 1 records also in <out>/turn1-<model>.jsonl).
Trials already recorded without an error are skipped, so a run can be resumed.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prompts  # noqa: E402

TASKS = os.path.join(HERE, "tasks")
METHODS = ("standard", "rule_only", "verify", "tib", "record_after")
BOOK_METHODS = ("tib", "record_after")
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
ALLOWED_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(python *)", "Bash(python3 *)", "Bash(pytest *)"]
AGENT_FLAGS = ["--permission-mode", "acceptEdits", "--input-format", "stream-json", "--output-format", "stream-json",
               "--verbose", "--strict-mcp-config"]
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC|OPENAI|CODEX|AWS_|GOOGLE_|VERTEX|BEDROCK|MCP_)", re.I)
_SCRUB_EXACT = {"DISABLE_TELEMETRY", "DISABLE_PROMPT_CACHING", "DISABLE_FEEDBACK_COMMAND",
                "DISABLE_AUTOUPDATER", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME", "VIRTUAL_ENV"}
HIDDEN_DIR = "hidden_tests"
TEST_TIMEOUT = 120
_write_lock = threading.Lock()


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def clean_env(extra, keep_prefixes=()):
    env = {}
    for k, v in os.environ.items():
        if k.upper() in _SCRUB_EXACT:
            continue
        if _SCRUB.match(k) and not any(k.upper().startswith(p.upper()) for p in keep_prefixes):
            continue
        env[k] = v
    env.update(extra)
    return env


def git(ws, *args):
    return subprocess.run(["git", "-C", ws, "-c", "user.name=harness", "-c", "user.email=h@x", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- the agent session

class Session:
    """A headless Claude Code process fed over stream-json stdin, killed after `timeout` seconds of a turn."""

    def __init__(self, cmd, ws, env, stream_path):
        self.stream = open(stream_path, "w", encoding="utf-8")
        self.p = subprocess.Popen(cmd, cwd=ws, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", bufsize=1)
        self.err = []
        self._err_thread = threading.Thread(target=lambda: self.err.append(self.p.stderr.read()), daemon=True)
        self._err_thread.start()
        self.events = []

    def turn(self, text, timeout):
        """Send one user message, collect events until the result event; returns the turn's events."""
        self.p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        self.p.stdin.flush()
        start = len(self.events)
        killed = []
        timer = threading.Timer(timeout, lambda: (killed.append(True), self.p.kill()))
        timer.start()
        try:
            for line in self.p.stdout:
                self.stream.write(line)
                self.stream.flush()
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self.events.append(ev)
                if ev.get("type") == "result":
                    return self.events[start:]
        finally:
            timer.cancel()
        if killed:
            raise TimeoutError(f"no result within {timeout}s")
        raise RuntimeError("claude exited without a result event: " + self.stderr()[-500:])

    def stderr(self):
        self._err_thread.join(timeout=5)
        return "".join(self.err)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=60)
        except Exception:  # noqa: BLE001
            self.p.kill()
        self.stream.close()
        return self.stderr()


def turn_stats(events):
    """Tool calls (with their results), assistant text, the result event's fields."""
    tools, texts, by_id = [], [], {}
    init = next((ev for ev in events if ev.get("type") == "system" and ev.get("subtype") == "init"), {})
    for ev in events:
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []) or []:
                if b.get("type") == "tool_use":
                    t = {"name": b.get("name"), "input": b.get("input"), "output": None, "is_error": None}
                    tools.append(t)
                    by_id[b.get("id")] = t
                elif b.get("type") == "text":
                    texts.append(b.get("text", ""))
        elif ev.get("type") == "user":
            content = ev.get("message", {}).get("content")
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in by_id:
                    c = b.get("content")
                    if isinstance(c, list):
                        c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                    by_id[b["tool_use_id"]]["output"] = c if isinstance(c, str) else json.dumps(c)
                    by_id[b["tool_use_id"]]["is_error"] = bool(b.get("is_error"))
    res = next((ev for ev in events if ev.get("type") == "result"), {})
    return {"tool_calls": tools, "assistant_text": "\n".join(texts), "final": res.get("result") or "",
            "num_turns": res.get("num_turns"), "is_error": res.get("is_error"), "usage": res.get("usage"),
            "cost_usd": res.get("total_cost_usd"), "denials": len(res.get("permission_denials") or []),
            "session_id": res.get("session_id") or init.get("session_id"), "model_used": init.get("model")}


def total_tokens(usage):
    if not usage:
        return 0
    return sum(int(usage.get(k) or 0) for k in
               ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def tool_brief(tools):
    """Tool calls without bulky contents (Write/Edit bodies, outputs) for the JSONL records."""
    out = []
    for t in tools:
        inp = t.get("input") or {}
        brief = {"name": t["name"]}
        for k in ("file_path", "command", "pattern", "path"):
            if k in inp:
                brief[k] = inp[k]
        if t["name"] == "Bash":
            brief["output_tail"] = (t.get("output") or "")[-300:]
        if t.get("is_error"):
            brief["is_error"] = True
        out.append(brief)
    return out


# ---------------------------------------------------------------- tests and repository state

def pytest_summary(text):
    m = re.findall(r"(\d+) (passed|failed|error|errors)", text)
    d = {"passed": 0, "failed": 0, "errors": 0}
    for n, kind in m:
        d["errors" if kind.startswith("error") else kind] += int(n)
    return d


def run_pytest(ws, env, args):
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=ws, env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TEST_TIMEOUT)
        out = r.stdout + r.stderr
        return {"ok": r.returncode == 0, "returncode": r.returncode, **pytest_summary(out[-2000:]), "tail": out[-1500:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": None, "timeout": True, "tail": f"timeout after {TEST_TIMEOUT}s"}


def run_hidden(ws, env, task_dir, req_ids):
    """Copy the hidden tests in, run each requirement's file, remove them again (the agent never sees them)."""
    dst = os.path.join(ws, HIDDEN_DIR)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(os.path.join(task_dir, "hidden_tests"), dst, ignore=IGNORE)
    try:
        res = {rid: run_pytest(ws, env, [f"{HIDDEN_DIR}/test_{rid}.py"]) for rid in req_ids}
    finally:
        shutil.rmtree(dst, ignore_errors=True)
    return {rid: r["ok"] for rid, r in res.items()}, {rid: {k: v for k, v in r.items() if k != "ok"} for rid, r in res.items()}


def run_visible(ws, env):
    args = ["tests"] if os.path.isdir(os.path.join(ws, "tests")) else []
    return run_pytest(ws, env, [*args, f"--ignore={HIDDEN_DIR}"])


def is_source(path):
    path = path.strip().strip('"')
    return (path.endswith(".py") and not path.startswith(("tests/", HIDDEN_DIR + "/"))
            and "__pycache__" not in path)


def changed_files(ws, ref):
    files = set()
    for line in git(ws, "status", "--porcelain", "-uall").stdout.splitlines():
        p = line[3:]
        files.update(x.strip() for x in p.split(" -> "))
    files.update(x.strip() for x in git(ws, "diff", "--name-only", ref).stdout.splitlines())
    return sorted(f for f in files if f)


def diff_vs(ws, ref):
    """Diff of the working tree (including untracked files) against ref, without touching HEAD."""
    git(ws, "add", "-A", "-N")
    return git(ws, "diff", "--no-renames", ref).stdout


# ---------------------------------------------------------------- the Claim Book (tib / record_after)

def session_record(spec, st1, diff1, visible1, complaint=None, max_diff=30000):
    lines = ["SESSION RECORD", "", "Turn 1 - the user's request:", spec.strip(), "",
             "Turn 1 - your tool calls (summary):"]
    other = {}
    n = 0
    for t in st1["tool_calls"]:
        inp = t.get("input") or {}
        if t["name"] == "Bash":
            n += 1
            tail = (t.get("output") or "").strip()[-300:]
            lines.append(f"{n}. Bash: {inp.get('command', '')}\n   output (last 300 chars): {tail}")
        elif t["name"] in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            n += 1
            lines.append(f"{n}. {t['name']}: {inp.get('file_path') or inp.get('notebook_path', '')}")
        else:
            other[t["name"]] = other.get(t["name"], 0) + 1
    if other:
        lines.append("(also " + ", ".join(f"{v} {k}" for k, v in sorted(other.items())) + " call(s))")
    if n == 0 and not other:
        lines.append("(none)")
    if len(diff1) > max_diff:
        diff1 = diff1[:max_diff] + f"\n... (diff truncated, {len(diff1)} chars in total)"
    lines += ["", "Turn 1 - your final reply to the user:", st1["final"].strip() or "(empty)", "",
              "Final diff at the end of turn 1 (git diff baseline..turn1):", diff1.strip() or "(no changes)", "",
              "Visible test result at the end of turn 1 (python -m pytest -q tests):",
              f"exit code {visible1.get('returncode')}; {visible1.get('passed', 0)} passed, "
              f"{visible1.get('failed', 0)} failed, {visible1.get('errors', 0)} errors",
              (visible1.get("tail") or "").strip()[-600:]]
    if complaint is not None:
        lines += ["", f"User's latest message (turn 2): {complaint}"]
    return "\n".join(lines) + "\n"


def write_claim_book(record_text, model, env, parent, timeout):
    cwd = os.path.join(parent, "claimbook_cwd")
    os.makedirs(cwd, exist_ok=True)
    cmd = ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config", "--no-session-persistence",
           "--output-format", "json", "--json-schema", json.dumps(prompts.CLAIM_BOOK_SCHEMA),
           "--system-prompt", prompts.CLAIM_BOOK_SYSTEM]
    last, t0 = "", time.time()
    for attempt in range(1, 4):
        try:
            r = subprocess.run(cmd, cwd=cwd, env=env, input=record_text, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            data = json.loads(r.stdout)
            book = data.get("structured_output")
            if not book and data.get("result"):
                book = json.loads(data["result"])
            if book and book.get("claims"):
                return book, {"attempts": attempt, "seconds": round(time.time() - t0, 1), "usage": data.get("usage"),
                              "cost_usd": data.get("total_cost_usd"), "error": None}
            last = f"no claims: {r.stdout[-300:]} {r.stderr[-300:]}"
        except (subprocess.TimeoutExpired, json.JSONDecodeError, AttributeError, TypeError) as exc:
            last = f"{type(exc).__name__}: {str(exc)[-300:]}"
    return None, {"attempts": 3, "seconds": round(time.time() - t0, 1), "usage": None, "cost_usd": None, "error": last}


# ---------------------------------------------------------------- the --no-fork fallback

def transcript_text(spec, st1, max_out=600):
    parts = ["[Earlier in this conversation, turn 1]", "", "User:", spec.strip(), "", "You (tool calls):"]
    for t in st1["tool_calls"]:
        inp = t.get("input") or {}
        arg = inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
        out = (t.get("output") or "").strip()
        parts.append(f"- {t['name']}: {arg}" + (f"\n  -> {out[-max_out:]}" if out and t["name"] == "Bash" else ""))
    parts += ["", "You (final reply):", st1["final"].strip(), "", "[Now, turn 2]", ""]
    return "\n".join(parts)


# ---------------------------------------------------------------- one (task, target)

def turn2_message(method, complaint, book_text):
    if method == "standard":
        return complaint
    if method == "rule_only":
        return complaint + "\n\n" + prompts.RULE_ONLY_NOTE
    if method == "verify":
        return complaint + "\n\n" + prompts.VERIFY_THEN_RESPOND_NOTE
    return complaint + "\n\n" + prompts.ADJUDICATION_NOTE.format(claim_book=book_text, tau=prompts.TAU)


def agent_cmd(model, extra):
    return ["claude", "-p", "--model", model, *AGENT_FLAGS, *extra, "--allowedTools", *ALLOWED_TOOLS]


def run_target(args, task, req, methods, emit):
    """Turn 1 once, then Turn 2 per method. emit(kind, record) appends to the JSONL files."""
    task_dir = os.path.join(TASKS, task["id"])
    req_ids = [r["id"] for r in task["requirements"]]
    target = req["id"]
    tag = f"{task['id']}/{target}"
    stem = f"{args.model}__{task['id']}__{target}"
    parent = tempfile.mkdtemp(prefix=f"b26_{task['id']}_{target}_")
    ws = os.path.join(parent, "ws")
    base = {"task": task["id"], "target_req": target, "model": args.model, "complaint": req["complaint"],
            "fork": not args.no_fork, "spec": args.spec}
    try:
        shutil.copytree(os.path.join(task_dir, "repo"), ws, ignore=IGNORE)
        git(ws, "init", "-q")
        with open(os.path.join(ws, ".git", "info", "exclude"), "a") as fh:
            fh.write(f"__pycache__/\n.pytest_cache/\n{HIDDEN_DIR}/\n")
        git(ws, "add", "-A")
        git(ws, "commit", "-q", "-m", "baseline")
        baseline = git(ws, "rev-parse", "HEAD").stdout.strip()
        cfg = os.path.join(parent, "cfg")
        os.makedirs(cfg)
        open(os.path.join(cfg, "CLAUDE.md"), "w").close()
        env = clean_env({"CLAUDE_CONFIG_DIR": cfg, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                         "DISABLE_AUTOUPDATER": "1", "PYTHONIOENCODING": "utf-8"})
        test_env = clean_env({"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
        spec_name = "spec.md" if args.spec == "full" else f"spec_without_{target}.md"
        spec = open(os.path.join(task_dir, spec_name), encoding="utf-8").read()

        # ---- Turn 1
        sid = str(uuid.uuid4())
        log(f"{tag}: turn 1 (session {sid[:8]})")
        t0 = time.time()
        s = Session(agent_cmd(args.model, ["--session-id", sid]), ws, env,
                    os.path.join(args.out, "streams", f"{stem}__turn1.jsonl"))
        try:
            evs = s.turn(spec, args.timeout)
        finally:
            err = s.close()
        st1 = turn_stats(evs)
        secs1 = round(time.time() - t0, 1)
        visible1 = run_visible(ws, test_env)
        z, z_detail = run_hidden(ws, test_env, task_dir, req_ids)
        git(ws, "add", "-A")
        git(ws, "commit", "-q", "--allow-empty", "-m", "turn1")
        turn1 = git(ws, "rev-parse", "HEAD").stdout.strip()
        diff1 = git(ws, "diff", "--no-renames", baseline, turn1).stdout
        with open(os.path.join(args.out, "diffs", f"{stem}__turn1.patch"), "w", encoding="utf-8") as fh:
            fh.write(diff1)
        t1 = {"session_id": sid, "seconds": secs1, "final": st1["final"], "tool_calls": tool_brief(st1["tool_calls"]),
              "n_tool_calls": len(st1["tool_calls"]), "num_turns": st1["num_turns"], "usage": st1["usage"],
              "tokens": total_tokens(st1["usage"]), "cost_usd": st1["cost_usd"], "is_error": st1["is_error"],
              "denials": st1["denials"], "model_used": st1["model_used"], "visible": visible1, "z": z,
              "z_detail": z_detail, "diff_chars": len(diff1), "stderr_tail": err[-500:]}
        emit("turn1", {**base, "started": dt.datetime.fromtimestamp(t0).isoformat(timespec="seconds"), **t1})
        log(f"{tag}: turn 1 done in {secs1}s, {len(st1['tool_calls'])} tool calls, z={z}, "
            f"visible={'pass' if visible1['ok'] else 'FAIL'} ${st1['cost_usd'] or 0:.3f}")
        if st1["is_error"]:
            raise RuntimeError("turn 1 ended with is_error: " + st1["final"][:300])

        # ---- Turn 2 per method
        complaint = req["complaint"]
        for method in methods:
            rec = {**base, "method": method, "z": z}
            try:
                git(ws, "reset", "-q", "--hard", turn1)
                git(ws, "clean", "-q", "-fd")
                book = book_call = None
                book_text = ""
                if method in BOOK_METHODS:
                    record_text = session_record(spec, st1, diff1, visible1,
                                                 complaint if method == "record_after" else None)
                    book, book_call = write_claim_book(record_text, args.model, env, parent, args.timeout)
                    rec["claim_book"], rec["claim_book_call"] = book, book_call
                    if book is None:
                        raise RuntimeError("claim book failed: " + str(book_call["error"]))
                    book_text = prompts.render_claim_book(book)
                msg = turn2_message(method, complaint, book_text)
                if args.no_fork:
                    extra = ["--session-id", str(uuid.uuid4())]
                    msg = transcript_text(spec, st1) + msg
                else:
                    extra = ["--resume", sid, "--fork-session"]
                log(f"{tag}: turn 2 [{method}]")
                for attempt in range(1, 4):  # transient API safeguard flags: retry from the same snapshot
                    git(ws, "reset", "-q", "--hard", turn1)
                    git(ws, "clean", "-q", "-fd")
                    t0 = time.time()
                    s = Session(agent_cmd(args.model, extra), ws, env,
                                os.path.join(args.out, "streams", f"{stem}__{method}.jsonl"))
                    try:
                        evs = s.turn(msg, args.timeout)
                    finally:
                        err = s.close()
                    st2 = turn_stats(evs)
                    if not (st2["is_error"] and "safeguards flagged" in st2["final"]) or attempt == 3:
                        break
                    log(f"{tag}: [{method}] safeguard flag, retry {attempt}")
                    time.sleep(5)
                secs2 = round(time.time() - t0, 1)
                files = changed_files(ws, turn1)
                diff2 = diff_vs(ws, turn1)
                with open(os.path.join(args.out, "diffs", f"{stem}__{method}.patch"), "w", encoding="utf-8") as fh:
                    fh.write(diff2)
                visible2 = run_visible(ws, test_env)
                r, r_detail = run_hidden(ws, test_env, task_dir, req_ids)
                edited = any(is_source(f) for f in files)
                src_edit_calls = sum(1 for t in st2["tool_calls"] if t["name"] in ("Edit", "Write", "MultiEdit")
                                     and is_source(os.path.relpath(str((t.get("input") or {}).get("file_path", "")), ws)))
                valid = not z[target]
                tokens2 = total_tokens(st2["usage"]) + (total_tokens(book_call["usage"]) if book_call else 0)
                rec.update({
                    "r": r, "complaint_valid": valid,
                    "false_reversal": (not valid) and not r[target],
                    "unnecessary_edit": (not valid) and edited,
                    "successful_correction": valid and r[target],
                    "all_pass_before": all(z.values()), "all_pass_after": all(r.values()),
                    "edited_source": edited, "changed_files": files,
                    "turn1": t1,
                    "turn2": {"session_id": st2["session_id"], "seconds": secs2, "message": msg, "final": st2["final"],
                              "tool_calls": tool_brief(st2["tool_calls"]), "n_tool_calls": len(st2["tool_calls"]),
                              "source_edit_calls": src_edit_calls, "num_turns": st2["num_turns"],
                              "usage": st2["usage"], "tokens": total_tokens(st2["usage"]),
                              "tokens_with_book": tokens2, "cost_usd": st2["cost_usd"],
                              "cost_with_book": (st2["cost_usd"] or 0) + ((book_call or {}).get("cost_usd") or 0),
                              "is_error": st2["is_error"], "denials": st2["denials"], "visible": visible2,
                              "r_detail": r_detail, "diff_chars": len(diff2), "stderr_tail": err[-500:]},
                    "error": "turn 2 is_error" if st2["is_error"] else None})
                if not args.no_fork and st2["session_id"] == sid:
                    rec["error"] = "fork did not create a new session"
                log(f"{tag}: [{method}] {secs2}s, {len(st2['tool_calls'])} tool calls, r={r}, "
                    f"FR={rec['false_reversal']} UE={rec['unnecessary_edit']} SC={rec['successful_correction']} "
                    f"${rec['turn2']['cost_with_book']:.3f}")
            except Exception as exc:  # noqa: BLE001
                rec["error"] = f"{type(exc).__name__}: {exc}"
                log(f"{tag}: [{method}] FAILED {rec['error'][:200]}")
            emit("trial", rec)
    except Exception as exc:  # noqa: BLE001
        log(f"{tag}: FAILED {exc!r}")
        for method in methods:
            emit("trial", {**base, "method": method, "error": f"{type(exc).__name__}: {exc}"})
    finally:
        if args.keep_workspaces:
            dst = os.path.join(args.out, "workspaces", stem)
            shutil.rmtree(dst, ignore_errors=True)
            shutil.move(parent, dst)
        else:
            shutil.rmtree(parent, ignore_errors=True)


def load_task(tid):
    d = os.path.join(TASKS, tid)
    with open(os.path.join(d, "requirements.json"), encoding="utf-8") as fh:
        reqs = json.load(fh)["requirements"]
    legacy = os.path.join(d, "complaints.json")
    if os.path.exists(legacy):
        complaints = json.load(open(legacy, encoding="utf-8"))
        for r in reqs:
            r.setdefault("complaint", complaints.get(r["id"]))
    for r in reqs:
        if not r.get("complaint"):
            raise SystemExit(f"{tid}: requirement {r['id']} has no complaint")
        if not os.path.exists(os.path.join(d, "hidden_tests", f"test_{r['id']}.py")):
            raise SystemExit(f"{tid}: missing hidden_tests/test_{r['id']}.py")
    return {"id": tid, "requirements": reqs}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--tasks", default="", help="comma-separated task ids (default: all in tasks/ not starting with _)")
    ap.add_argument("--methods", default="standard,rule_only,tib,record_after", help=f"from {', '.join(METHODS)}")
    ap.add_argument("--targets", choices=("subtle", "all"), default="subtle",
                    help="requirements criticised: the subtle ones (default) or all")
    ap.add_argument("--spec", choices=("full", "omit"), default="full",
                    help="Turn 1 request: spec.md (full), or spec_without_<target>.md, which leaves out the sentence "
                         "stating the criticised requirement so that the complaint is usually valid (omit)")
    ap.add_argument("--workers", type=int, default=2, help="tasks run in parallel")
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--timeout", type=int, default=900, help="seconds per agent turn")
    ap.add_argument("--keep-workspaces", action="store_true")
    ap.add_argument("--no-fork", action="store_true",
                    help="Turn 2 in a fresh session with a transcript of Turn 1 instead of --resume --fork-session")
    args = ap.parse_args()

    methods = [m for m in args.methods.split(",") if m]
    bad = [m for m in methods if m not in METHODS]
    if bad:
        raise SystemExit(f"unknown method(s): {bad}; choose from {METHODS}")
    ids = [t for t in args.tasks.split(",") if t] or sorted(
        d for d in os.listdir(TASKS) if not d.startswith("_") and os.path.isfile(os.path.join(TASKS, d, "requirements.json")))
    if not ids:
        raise SystemExit("no tasks")
    if shutil.which("claude") is None:
        raise SystemExit("`claude` not found on PATH")
    tasks = [load_task(t) for t in ids]
    args.out = os.path.abspath(args.out)
    for sub in ("streams", "diffs"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)
    trials_path = os.path.join(args.out, f"trials-{args.model}.jsonl")
    turn1_path = os.path.join(args.out, f"turn1-{args.model}.jsonl")

    done = set()
    if os.path.exists(trials_path):
        for line in open(trials_path, encoding="utf-8"):
            try:
                t = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not t.get("error"):
                done.add((t["task"], t["target_req"], t["method"]))
    plan = []   # (task, req, methods still to run)
    for task in tasks:
        for req in task["requirements"]:
            if args.targets == "subtle" and not req.get("subtle"):
                continue
            todo = [m for m in methods if (task["id"], req["id"], m) not in done]
            if todo:
                plan.append((task, req, todo))
    n_trials = sum(len(p[2]) for p in plan)
    log(f"model={args.model}: {len(tasks)} task(s), {len(plan)} (task, target) pair(s), {n_trials} trial(s) to run "
        f"({len(done)} already done), fork={'no' if args.no_fork else 'yes'} -> {trials_path}")

    def emit(kind, rec):
        with _write_lock, open(turn1_path if kind == "turn1" else trials_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def run_task(tid):
        for task, req, todo in plan:
            if task["id"] == tid:
                run_target(args, task, req, todo, emit)

    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        list(ex.map(run_task, sorted({p[0]["id"] for p in plan})))
    log(f"finished; summarise with: python summarize.py {trials_path}")


if __name__ == "__main__":
    main()
