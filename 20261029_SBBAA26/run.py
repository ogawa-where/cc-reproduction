#!/usr/bin/env python3
"""Reproduce Q3/Q4 of arXiv:2610.31778 (Salle et al. 2026, "Benchmarks Are Surprisingly
Compaction-Friendly") with Claude Code: does the compaction summary keep what to build but drop
how to work and what not to touch?

One run = one scripted multi-turn Claude Code session on a small repository:
  1. the user gives a task plus planted constraints over several turns (scenario.json);
  2. the agent works (headless `claude -p`, stream-json in/out, acceptEdits, Bash limited to python/pytest);
  3. the context is compacted (`/compact`, or Claude Code's auto-compaction with --autocompact);
  4. the compaction summary is extracted from the stream / transcript;
  5. the paper's preservation judge (Appendix 6.4.5, Sonnet, sees only summary + constraints)
     labels each planted constraint preserved / dropped / contradicted;
  6. a probe turn continues the task and mechanical checks record whether scope exclusions and
     process instructions were still honoured after compaction.
Records go to <out>/runs.jsonl; `python summarize.py <out>/runs.jsonl` aggregates by category.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = os.path.join(HERE, "scenarios")
PROMPTS = os.path.join(HERE, "prompts")
IGNORE = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache")
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC|OPENAI|CODEX|AWS_|GOOGLE_|VERTEX|BEDROCK|MCP_)", re.I)
_SCRUB_EXACT = {"DISABLE_TELEMETRY", "DISABLE_PROMPT_CACHING", "DISABLE_FEEDBACK_COMMAND",
                "DISABLE_AUTOUPDATER", "PYTHONPATH", "PYTHONSTARTUP", "PYTHONHOME", "VIRTUAL_ENV"}
AGENT_FLAGS = ["--permission-mode", "acceptEdits", "--input-format", "stream-json",
               "--output-format", "stream-json", "--verbose", "--strict-mcp-config",
               "--allowedTools", "Bash(python *)", "Bash(python3 *)", "Bash(pytest *)",
               "--disallowedTools", "Bash(pip *)", "Bash(python -m pip *)", "Bash(python3 -m pip *)",
               "Bash(git commit*)"]
PRESERVATION_SCHEMA = json.dumps({
    "type": "object", "additionalProperties": False, "required": ["verdicts"],
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["id", "reasoning", "verdict", "evidence", "confidence"],
        "properties": {"id": {"type": "string"}, "reasoning": {"type": "string"},
                       "verdict": {"type": "string", "enum": ["preserved", "dropped", "contradicted"]},
                       "evidence": {"type": "string"},
                       "confidence": {"type": "string", "enum": ["high", "medium", "low"]}}}}}})
CLASSIFICATION_SCHEMA = json.dumps({
    "type": "object", "additionalProperties": False, "required": ["items"],
    "properties": {"items": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["id", "reasoning", "category", "confidence"],
        "properties": {"id": {"type": "string"}, "reasoning": {"type": "string"},
                       "category": {"type": "string", "enum": [
                           "scope_exclusion", "technical_parameter", "feature_requirement", "process_instruction",
                           "named_source_or_tool", "structural_convention", "soft_preference", "other"]},
                       "confidence": {"type": "string", "enum": ["high", "medium", "low"]}}}}}})


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


def git(ws, *args):
    return subprocess.run(["git", "-C", ws, "-c", "user.name=baseline", "-c", "user.email=b@x", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- the agent session

class Session:
    """A headless Claude Code session fed over stream-json stdin."""

    def __init__(self, ws, env, model, autocompact, stream_path, claude_bin="claude"):
        cmd = [claude_bin, "-p", "--model", model, *AGENT_FLAGS]
        if autocompact:
            cmd += ["--autocompact", str(autocompact)]
        self.stream = open(stream_path, "w", encoding="utf-8")
        self.p = subprocess.Popen(cmd, cwd=ws, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", bufsize=1)
        self.events = []
        self.compactions = []       # indexes into self.events of compact_boundary events
        self.summaries = []         # summary texts (stream user event after each boundary)
        self._expect_summary = False

    def send(self, text):
        self.p.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        self.p.stdin.flush()

    def turn(self, text, timeout):
        """Send one user message and collect events until the result event. Returns the events of the turn."""
        self.send(text)
        start = len(self.events)
        t0 = time.time()
        while time.time() - t0 < timeout:
            line = self.p.stdout.readline()
            if not line:
                break
            self.stream.write(line)
            self.stream.flush()
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.events.append(ev)
            t = ev.get("type")
            if t == "system" and ev.get("subtype") == "compact_boundary":
                self.compactions.append(len(self.events) - 1)
                self._expect_summary = True
            elif t == "user" and self._expect_summary:
                content = ev.get("message", {}).get("content")
                if isinstance(content, str) and "summary" in content.lower():
                    self.summaries.append(content)
                    self._expect_summary = False
            if t == "result":
                return self.events[start:]
        raise TimeoutError(f"no result within {timeout}s")

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=60)
        except Exception:  # noqa: BLE001
            self.p.kill()
        err = self.p.stderr.read() if self.p.stderr else ""
        self.stream.close()
        return err


def render_turn(spec):
    """A turn is a string, or {"text": ..., "paste": {"kind", "seed", "kb"}} with a long paste appended."""
    if isinstance(spec, str):
        return spec
    text = spec["text"]
    if spec.get("paste"):
        p = spec["paste"]
        text += "\n\n```\n" + fixtures.make(p["kind"], p["seed"], p["kb"]) + "\n```"
    return text


def turn_stats(events):
    tools, texts = [], []
    for ev in events:
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []) or []:
                if b.get("type") == "tool_use":
                    tools.append({"name": b.get("name"), "input": b.get("input")})
                elif b.get("type") == "text":
                    texts.append(b.get("text", ""))
    res = next((ev for ev in events if ev.get("type") == "result"), {})
    return {"tool_calls": tools, "assistant_text": "\n".join(texts), "num_turns": res.get("num_turns"),
            "is_error": res.get("is_error"), "usage": res.get("usage"), "denials": len(res.get("permission_denials") or [])}


def summary_body(text):
    """The summary proper: drop the harness wrapper around it so the judge sees what the agent wrote."""
    body = text
    m = re.search(r"\nSummary:\n", body)
    if m:
        body = body[m.end():]
    cut = body.find("\nIf you need specific details from before compaction")
    if cut >= 0:
        body = body[:cut]
    return body.strip()


def transcript_summaries(cfg):
    out = []
    for path in glob.glob(os.path.join(cfg, "projects", "*", "*.jsonl")):
        for line in open(path, encoding="utf-8", errors="replace"):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("isCompactSummary"):
                c = e.get("message", {}).get("content")
                out.append(c if isinstance(c, str) else "".join(b.get("text", "") for b in c if isinstance(b, dict)))
    return out


# ---------------------------------------------------------------- judges

def call_judge(system_prompt, schema, user_text, model, env, parent, timeout=600):
    cfg = os.path.join(parent, "judge_cfg")
    os.makedirs(cfg, exist_ok=True)
    open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "judge_cwd")
    os.makedirs(cwd, exist_ok=True)
    cmd = ["claude", "-p", "--model", model, "--safe-mode", "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "json", "--json-schema", schema,
           "--system-prompt", system_prompt]
    jenv = dict(env, CLAUDE_CONFIG_DIR=cfg)
    last = ""
    for _ in range(3):
        try:
            r = subprocess.run(cmd, cwd=cwd, env=jenv, input=user_text, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
            data = json.loads(r.stdout)
            obj = data.get("structured_output") or json.loads(data.get("result") or "{}")
            if obj:
                return obj, None
            last = f"empty structured output: {r.stdout[-300:]}"
        except (subprocess.TimeoutExpired, json.JSONDecodeError, AttributeError) as exc:
            last = f"{type(exc).__name__}: {str(exc)[-300:]}"
    return None, last


def judge_preservation(summary, constraints, model, env, parent):
    prompt = open(os.path.join(PROMPTS, "preservation.md"), encoding="utf-8").read()
    user = ("COMPACTION SUMMARY:\n---\n" + summary + "\n---\n\nCONSTRAINTS (JSON):\n"
            + json.dumps([{"id": c["id"], "text": c["text"]} for c in constraints], ensure_ascii=False, indent=1))
    obj, err = call_judge(prompt, PRESERVATION_SCHEMA, user, model, env, parent)
    if not obj:
        return {c["id"]: {"verdict": None, "error": err} for c in constraints}
    return {v["id"]: v for v in obj.get("verdicts", [])}


def judge_classification(constraints, model, env, parent):
    prompt = open(os.path.join(PROMPTS, "classification.md"), encoding="utf-8").read()
    user = "ITEMS (JSON):\n" + json.dumps([{"id": c["id"], "text": c["text"]} for c in constraints],
                                           ensure_ascii=False, indent=1)
    obj, err = call_judge(prompt, CLASSIFICATION_SCHEMA, user, model, env, parent)
    if not obj:
        return {c["id"]: {"category": None, "error": err} for c in constraints}
    return {v["id"]: v for v in obj.get("items", [])}


# ---------------------------------------------------------------- mechanical checks after the probe turn

def mechanical_checks(ws, scenario, probe_events):
    checks = scenario.get("checks", {})
    out = {}
    changed = set(l.strip() for l in git(ws, "diff", "--name-only", "HEAD").stdout.splitlines())
    git(ws, "add", "-A")
    changed |= set(l.strip() for l in git(ws, "diff", "--cached", "--name-only", "HEAD").stdout.splitlines())
    deleted = set(l.strip() for l in git(ws, "diff", "--cached", "--name-only", "--diff-filter=D", "HEAD").stdout.splitlines())
    if "untouched_files" in checks:
        out["untouched_files_modified"] = sorted(f for f in checks["untouched_files"] if f in changed)
    if "existing_tests_kept" in checks:
        out["existing_tests_removed"] = sorted(f for f in checks["existing_tests_kept"] if f in deleted or not os.path.exists(os.path.join(ws, f)))
    tools = turn_stats(probe_events)["tool_calls"]
    bash = [t["input"].get("command", "") for t in tools if t["name"] == "Bash" and isinstance(t["input"], dict)]
    if checks.get("pytest_after_probe"):
        out["pytest_run_in_probe"] = any("pytest" in c for c in bash)
    if checks.get("no_git_commit"):
        out["git_commit_attempted"] = any("git commit" in c for c in bash)
    if checks.get("no_new_test_files"):
        added = set(l.strip() for l in git(ws, "diff", "--cached", "--name-only", "--diff-filter=A", "HEAD").stdout.splitlines())
        out["new_test_files"] = sorted(f for f in added if f.startswith("tests/") and f.endswith(".py"))
    return out


# ---------------------------------------------------------------- one run

def one_run(args, scenario, rep, out_dir, keep_prefixes):
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{scenario['id']}-r{rep}-{stamp}"
    art = os.path.join(out_dir, run_id)
    os.makedirs(art, exist_ok=True)
    parent = tempfile.mkdtemp(prefix=f"compact_{run_id}_")
    rec = {"run": run_id, "scenario": scenario["id"], "rep": rep, "model": args.model, "judge_model": args.judge_model,
           "compact_mode": "auto" if args.autocompact else "manual", "autocompact": args.autocompact,
           "valid": True, "failures": [], "started": dt.datetime.now().isoformat(timespec="seconds")}
    try:
        ws = os.path.join(parent, "ws")
        shutil.copytree(os.path.join(SCENARIOS, scenario["id"], "repo"), ws, ignore=IGNORE)
        git(ws, "init", "-q")
        with open(os.path.join(ws, ".git", "info", "exclude"), "a") as fh:
            fh.write("__pycache__/\n.pytest_cache/\n")
        git(ws, "add", "-A")
        git(ws, "commit", "-q", "-m", "baseline")
        cfg = os.path.join(parent, "cfg")
        os.makedirs(cfg)
        open(os.path.join(cfg, "CLAUDE.md"), "w").close()
        if args.copy_credentials:
            src = os.path.join(os.path.expanduser(args.copy_credentials), ".credentials.json")
            if not os.path.exists(src):
                raise FileNotFoundError(f"no .credentials.json in {args.copy_credentials}; run `/login` with that CLAUDE_CONFIG_DIR first")
            shutil.copyfile(src, os.path.join(cfg, ".credentials.json"))
            os.chmod(os.path.join(cfg, ".credentials.json"), 0o600)
        env = clean_env(keep_prefixes, {"CLAUDE_CONFIG_DIR": cfg, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
                                        "DISABLE_AUTOUPDATER": "1", "PYTHONIOENCODING": "utf-8"})
        log(f"{run_id}: start")
        s = Session(ws, env, args.model, args.autocompact, os.path.join(art, "stream.jsonl"), args.claude_bin)
        turns = []
        t0 = time.time()
        for i, spec in enumerate(scenario["turns"], start=1):
            text = render_turn(spec)
            evs = s.turn(text, args.turn_timeout)
            st = turn_stats(evs)
            turns.append({"index": i, "kind": "task", **{k: st[k] for k in ("num_turns", "is_error", "usage", "denials")},
                          "tool_calls": len(st["tool_calls"]), "compactions_so_far": len(s.compactions)})
            log(f"{run_id}: turn {i} done, {len(st['tool_calls'])} tool calls, compactions so far {len(s.compactions)}")
        if not s.compactions:
            if args.autocompact:
                rec["failures"].append({"stage": "compaction", "reason": "auto-compaction never triggered; forcing /compact"})
            evs = s.turn("/compact", args.turn_timeout)
            turns.append({"index": len(turns) + 1, "kind": "compact", "tool_calls": 0,
                          "compactions_so_far": len(s.compactions)})
        if not s.compactions:
            raise RuntimeError("no compaction happened")
        rec["compaction_index_turn"] = next(i for i, t in enumerate(turns, start=1) if t["compactions_so_far"] > 0)
        boundary = s.events[s.compactions[0]]
        rec["compact_metadata"] = boundary.get("compact_metadata")
        rec["n_compactions"] = len(s.compactions)
        summary_full = s.summaries[0] if s.summaries else (transcript_summaries(cfg) or [""])[0]
        rec["summary_full"] = summary_full
        rec["summary"] = summary_body(summary_full)
        with open(os.path.join(art, "summary.md"), "w", encoding="utf-8") as fh:
            fh.write(summary_full)
        # probe turn after compaction
        evs = s.turn(scenario["probe_turn"], args.turn_timeout)
        st = turn_stats(evs)
        turns.append({"index": len(turns) + 1, "kind": "probe", **{k: st[k] for k in ("num_turns", "is_error", "usage", "denials")},
                      "tool_calls": len(st["tool_calls"]), "compactions_so_far": len(s.compactions)})
        rec["probe_reply"] = st["assistant_text"]
        rec["checks"] = mechanical_checks(ws, scenario, evs)
        # further compaction rounds (paper Q3: loss compounds as summaries are written from summaries)
        extra = scenario.get("extra_turns", [])
        for k in range(2, args.compactions + 1):
            spec = extra[(k - 2) % len(extra)] if extra else "Please continue with anything left to do."
            evs = s.turn(render_turn(spec), args.turn_timeout)
            st = turn_stats(evs)
            turns.append({"index": len(turns) + 1, "kind": f"extra{k}", **{kk: st[kk] for kk in ("num_turns", "is_error", "usage", "denials")},
                          "tool_calls": len(st["tool_calls"]), "compactions_so_far": len(s.compactions)})
            before = len(s.compactions)
            if len(s.compactions) < k:
                s.turn("/compact", args.turn_timeout)
                turns.append({"index": len(turns) + 1, "kind": "compact", "tool_calls": 0, "compactions_so_far": len(s.compactions)})
            log(f"{run_id}: compaction round {k} done ({len(s.compactions)} compactions so far)")
        err = s.close()
        rec["n_compactions"] = len(s.compactions)
        rec["turns"] = turns
        rec["seconds"] = round(time.time() - t0, 1)
        if err.strip():
            with open(os.path.join(art, "stderr.txt"), "w", encoding="utf-8") as fh:
                fh.write(err)
        diff = git(ws, "diff", "--cached", "--no-renames", "HEAD").stdout
        with open(os.path.join(art, "diff.patch"), "w", encoding="utf-8") as fh:
            fh.write(diff)
        # judges: constraints given before the compaction are the ones at stake
        at_stake = [c for c in scenario["constraints"] if c["turn"] <= rec["compaction_index_turn"]]
        if not rec["summary"]:
            raise RuntimeError("empty compaction summary")
        log(f"{run_id}: judging {len(at_stake)} constraints")
        verdicts = judge_preservation(rec["summary"], at_stake, args.judge_model, env, parent)
        rec["constraints"] = []
        for c in at_stake:
            v = verdicts.get(c["id"], {})
            rec["constraints"].append({**c, "verdict": v.get("verdict"), "evidence": v.get("evidence", ""),
                                       "confidence": v.get("confidence"), "reasoning": v.get("reasoning", ""),
                                       "error": v.get("error")})
        all_summaries = s.summaries if len(s.summaries) >= len(s.compactions) else transcript_summaries(cfg)
        rec["summaries"] = [summary_body(t) for t in all_summaries]
        rec["rounds"] = []
        for k, text in enumerate(rec["summaries"], start=1):
            if k == 1:
                vs = {c["id"]: c for c in rec["constraints"]}
            else:
                log(f"{run_id}: judging summary {k}")
                vs = judge_preservation(text, at_stake, args.judge_model, env, parent)
                with open(os.path.join(art, f"summary{k}.md"), "w", encoding="utf-8") as fh:
                    fh.write(all_summaries[k - 1])
            rec["rounds"].append({"compaction": k, "verdicts": [
                {"id": c["id"], "category": c["category"], "verdict": vs.get(c["id"], {}).get("verdict"),
                 "evidence": vs.get(c["id"], {}).get("evidence", "")} for c in at_stake]})
        if args.classify:
            cls = judge_classification(at_stake, args.judge_model, env, parent)
            for c in rec["constraints"]:
                c["judge_category"] = cls.get(c["id"], {}).get("category")
        n_drop = sum(1 for c in rec["constraints"] if c["verdict"] in ("dropped", "contradicted"))
        log(f"{run_id}: done in {rec['seconds']}s, pre_tokens={rec['compact_metadata'].get('pre_tokens') if rec['compact_metadata'] else None}, "
            f"dropped {n_drop}/{len(rec['constraints'])}, checks={rec['checks']}")
    except Exception as exc:  # noqa: BLE001
        rec["valid"] = False
        rec["failures"].append({"stage": "harness", "error": repr(exc)})
        log(f"{run_id}: FAILED {exc!r}")
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
    ap.add_argument("--scenarios", default="", help="comma-separated scenario ids (default: all)")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--model", default="sonnet", help="model for the tested agent (its own compaction summary)")
    ap.add_argument("--judge-model", default="sonnet", help="model for the judges (paper: Claude Sonnet 5)")
    ap.add_argument("--autocompact", type=int, default=0,
                    help="trigger Claude Code's auto-compaction at this many tokens (100000-1000000) instead of /compact")
    ap.add_argument("--compactions", type=int, default=1,
                    help="number of compaction rounds; rounds after the first feed the scenario's extra_turns and compact again")
    ap.add_argument("--classify", action="store_true", help="also run the paper's category classifier on the planted constraints")
    ap.add_argument("--turn-timeout", type=int, default=1200)
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--keep-env", default="", help="env-var prefixes to keep although they are scrubbed by default")
    ap.add_argument("--keep-workspaces", action="store_true")
    ap.add_argument("--claude-bin", default="claude", help="Claude Code executable for the tested agent (e.g. an older release)")
    ap.add_argument("--copy-credentials", default="",
                    help="config dir whose .credentials.json is copied into each run's fresh CLAUDE_CONFIG_DIR "
                         "(needed when the tested binary is logged in via a config dir, e.g. ~/.claude-old or ~/.claude)")
    args = ap.parse_args()
    ids = [s for s in args.scenarios.split(",") if s] or sorted(
        d for d in os.listdir(SCENARIOS) if os.path.isfile(os.path.join(SCENARIOS, d, "scenario.json")))
    if os.sep in args.claude_bin or "/" in args.claude_bin:
        args.claude_bin = os.path.abspath(args.claude_bin)   # the agent runs with cwd set to a temp workspace
    if shutil.which(args.claude_bin) is None:
        sys.exit(f"{args.claude_bin} not found")
    os.makedirs(args.out, exist_ok=True)
    keep = [p for p in args.keep_env.split(",") if p]
    log(f"{len(ids)} scenario(s) x {args.reps} rep(s), compaction={'auto@' + str(args.autocompact) if args.autocompact else 'manual'} -> {args.out}/runs.jsonl")
    for rep in range(1, args.reps + 1):
        for sid in ids:
            with open(os.path.join(SCENARIOS, sid, "scenario.json"), encoding="utf-8") as fh:
                scenario = json.load(fh)
            one_run(args, scenario, rep, args.out, keep)
    log("finished; summarise with: python summarize.py " + os.path.join(args.out, "runs.jsonl"))


if __name__ == "__main__":
    main()
