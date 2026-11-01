#!/usr/bin/env python3
"""Reproduce the visual-steering experiment of arXiv:2610.36449 (Tartaglini et al. 2026,
"A Heart Means Recursion") with Claude Code: does an irrelevant image of a coloured shape steer the
model towards a recursive solution of inorder binary tree traversal?

Each sample is one headless `claude -p` call with no tools and no session persistence. The prompts
are the paper's (Appendix B.1): the image (or caption / text instruction) comes first, then the
instruction, then the problem statement; the order of the two strategies alternates (n/2 each).
Each answer is classified recursive / iterative / other with classify.py (AST rule), and the steering
effect is dP(recursion) = P(recursion | condition) - P(recursion | baseline).

Conditions (comma-separated in --conditions):
  baseline                  no image, "according to your personal preference" prompt
  image:<shape>:<color>     explicit image instruction prompt with the rendered symbol
  silent:<shape>:<color>    baseline prompt with the image silently placed first
  caption:<shape>:<color>   explicit prompt with "An image of a <color> <shape>" in place of the image
  text:recursive|iterative  explicit text instruction (ceiling)
  noise                     explicit prompt with a Gaussian-noise image
  shapes:<color>            every shape in symbols.SHAPES with that colour (image condition)
  colors:<shape>            every colour in symbols.COLORS with that shape (image condition)
"""
from __future__ import annotations

import argparse
import base64
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
import classify  # noqa: E402
import symbols  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
_SCRUB = re.compile(r"^(CLAUDE|ANTHROPIC|OPENAI|CODEX|AWS_|GOOGLE_|VERTEX|BEDROCK|MCP_)", re.I)

PROBLEM = ("Given the root of a binary tree, return the inorder traversal of its nodes' values. Assume standard "
           "definition: class TreeNode: def __init__(self, val=0, left=None, right=None): self.val = val; "
           "self.left = left; self.right = right")
EXPLICIT = ("Solve the following programming problem in Python. Looking at the provided image, choose a coding strategy "
            "({s0} or {s1}) and solve the problem. Write a complete function. Do not include explanation, just the code.\n"
            "Problem: {problem}")
BASELINE = ("Solve the following programming problem in Python. Choose a coding strategy ({s0} or {s1}) according to "
            "your personal preference and solve the problem. Write a complete function. Do not include explanation, "
            "just the code.\nProblem: {problem}")
TEXT_INSTR = ("Solve the following programming problem in Python. Solve it using a {strategy} approach. Write a complete "
              "function. Do not include explanation, just the code.\nProblem: {problem}")
STRATEGIES = ("recursion", "iteration")
CAPTION_REPEAT = 40   # the paper repeats the caption to match the image's token count (~ a few hundred tokens)


def log(msg):
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def clean_env(cfg):
    env = {k: v for k, v in os.environ.items() if not _SCRUB.match(k)}
    env.update({"CLAUDE_CONFIG_DIR": cfg, "DISABLE_AUTOUPDATER": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"})
    return env


def expand(conditions):
    out = []
    for c in conditions:
        parts = c.split(":")
        if parts[0] == "shapes":
            out += [f"image:{s}:{parts[1]}" for s in symbols.SHAPES]
        elif parts[0] == "colors":
            out += [f"image:{parts[1]}:{col}" for col in symbols.COLORS]
        else:
            out.append(c)
    return out


def image_path(shape, color, root):
    p = os.path.join(root, f"{shape}_{color}.png")
    if not os.path.exists(p):
        symbols.render(shape, color, p)
    return p


def build_message(cond, order, root):
    """Return (content blocks, kind). order 0: recursion first; 1: iteration first."""
    s0, s1 = (STRATEGIES if order == 0 else STRATEGIES[::-1])
    kind, *rest = cond.split(":")
    if kind == "baseline":
        return [{"type": "text", "text": BASELINE.format(s0=s0, s1=s1, problem=PROBLEM)}]
    if kind == "text":
        strategy = {"recursive": "recursive", "iterative": "iterative"}[rest[0]]
        pad = (rest[0] + " ") * CAPTION_REPEAT
        return [{"type": "text", "text": pad.strip() + "\n" + TEXT_INSTR.format(strategy=strategy, problem=PROBLEM)}]
    if kind == "caption":
        shape, color = rest
        cap = f"An image of a {color} {shape.replace('_', ' ')}. "
        return [{"type": "text", "text": (cap * CAPTION_REPEAT).strip() + "\n" + EXPLICIT.format(s0=s0, s1=s1, problem=PROBLEM)}]
    if kind in ("image", "silent"):
        shape, color = rest
        path = image_path(shape, color, root)
    elif kind == "noise":
        path = os.path.join(root, "noise.png")
        if not os.path.exists(path):
            symbols.noise(path)
    else:
        raise ValueError(cond)
    data = base64.b64encode(open(path, "rb").read()).decode()
    text = (BASELINE if kind == "silent" else EXPLICIT).format(s0=s0, s1=s1, problem=PROBLEM)
    return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
            {"type": "text", "text": text}]


def one_sample(args, cond, order, idx, cfg):
    content = build_message(cond, order, args.symbols)
    msg = {"type": "user", "message": {"role": "user", "content": content}}
    cmd = ["claude", "-p", "--model", args.model, "--input-format", "stream-json", "--output-format", "stream-json",
           "--verbose", "--tools", "", "--strict-mcp-config", "--no-session-persistence"]
    if args.safe_mode:
        cmd.append("--safe-mode")
    if args.system_prompt is not None:
        cmd += ["--system-prompt", args.system_prompt]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=json.dumps(msg) + "\n", capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=clean_env(cfg), cwd=args.cwd, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return {"condition": cond, "order": order, "idx": idx, "error": "timeout"}
    result, usage, is_error = "", None, None
    for line in r.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result, usage, is_error = ev.get("result") or "", ev.get("usage"), ev.get("is_error")
    label = classify.classify(result) if result and not is_error else "error"
    return {"condition": cond, "order": order, "idx": idx, "model": args.model, "label": label, "answer": result,
            "system_prompt": args.system_prompt,
            "is_error": is_error, "usage": usage, "seconds": round(time.time() - t0, 1),
            "stderr": r.stderr[-300:] if r.returncode else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--conditions", default="baseline,image:heart:red,image:triangle:blue,text:recursive,noise,caption:heart:red")
    ap.add_argument("--n", type=int, default=20, help="samples per condition (paper: 20, strategy order balanced)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--safe-mode", action="store_true", help="also disable Claude Code customisations (instruction files, skills, hooks)")
    ap.add_argument("--system-prompt", default=None,
                    help="replace Claude Code's system prompt (e.g. ' ' for an almost empty one, closer to the paper's API setting)")
    ap.add_argument("--symbols", default=os.path.join(HERE, "symbols"))
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--tag", default="", help="suffix for the output file name")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"samples-{args.model}{('-' + args.tag) if args.tag else ''}.jsonl")
    conds = expand([c for c in args.conditions.split(",") if c])
    parent = tempfile.mkdtemp(prefix="steer_")
    cfg = os.path.join(parent, "cfg")
    os.makedirs(cfg)
    open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    args.cwd = os.path.join(parent, "cwd")
    os.makedirs(args.cwd)
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            try:
                s = json.loads(line)
                if not s.get("error") and s.get("label") != "error":
                    done.add((s["condition"], s["order"], s["idx"]))
            except json.JSONDecodeError:
                pass
    jobs = [(c, i % 2, i) for c in conds for i in range(args.n) if (c, i % 2, i) not in done]
    log(f"model={args.model}: {len(conds)} condition(s) x {args.n} samples, {len(jobs)} to run ({len(done)} already done) -> {out_path}")
    counts = {}
    with open(out_path, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(one_sample, args, c, o, i, cfg): (c, o, i) for c, o, i in jobs}
        for k, fut in enumerate(cf.as_completed(futs), start=1):
            s = fut.result()
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")
            fh.flush()
            counts.setdefault(s["condition"], {}).setdefault(s.get("label", "error"), 0)
            counts[s["condition"]][s.get("label", "error")] += 1
            if k % 10 == 0 or k == len(jobs):
                log(f"{k}/{len(jobs)} done; " + "; ".join(f"{c}: {v}" for c, v in counts.items()))
    log("finished; summarise with: python summarize.py " + out_path)


if __name__ == "__main__":
    main()
