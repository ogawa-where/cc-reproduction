#!/usr/bin/env python3
"""E3: robust vs fragile steering symbols. Single `claude -p` calls (no tools) on inorder binary tree traversal,
varying the symbol (spiral, branching_arrows, heart; red), where the image sits in the context and the wording.

position  first    image block first in the user message, one-sentence system prompt (closest to the paper)
          default  image block first, Claude Code's own system prompt (what a Claude Code user gets)
          after    Claude Code's system prompt, text first and the image block after it
wording   explicit the paper's prompt ("Looking at the provided image, choose a coding strategy ...")
          neutral  the paper's variation 3 ("... using either a recursive or iterative strategy", no "choose")
          ordinary no mention of strategies at all ("The image is attached for context")
Baselines (no image) are run for every position x wording. Samples: <out>/samples-e3-<model>.jsonl
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import json
import os
import sys
import tempfile
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPRO = os.path.join(os.path.dirname(HERE), "20261101_TWWWKL26")
sys.path.insert(0, REPRO)
import classify  # noqa: E402
import symbols  # noqa: E402
from run import PROBLEM, STRATEGIES, clean_env, log  # noqa: E402

MINIMAL_SYSTEM = "You are a helpful assistant."
WORDING = {
    "explicit": ("Solve the following programming problem in Python. Looking at the provided image, choose a coding strategy "
                 "({s0} or {s1}) and solve the problem. Write a complete function. Do not include explanation, just the code.\n"
                 "Problem: {problem}"),
    "neutral": ("Based on the provided image, write a complete Python function to solve the following programming problem "
                "using either a {s0_adj} or {s1_adj} strategy. Respond with code only and no explanation.\nProblem: {problem}"),
    "ordinary": ("Write a complete Python function to solve the following programming problem. The image is attached for "
                 "context. Respond with code only and no explanation.\nProblem: {problem}"),
}
BASELINE = {
    "explicit": ("Solve the following programming problem in Python. Choose a coding strategy ({s0} or {s1}) according to "
                 "your personal preference and solve the problem. Write a complete function. Do not include explanation, "
                 "just the code.\nProblem: {problem}"),
    "neutral": ("Write a complete Python function to solve the following programming problem using either a {s0_adj} or "
                "{s1_adj} strategy. Respond with code only and no explanation.\nProblem: {problem}"),
    "ordinary": ("Write a complete Python function to solve the following programming problem. Respond with code only and "
                 "no explanation.\nProblem: {problem}"),
}
ADJ = {"recursion": "recursive", "iteration": "iterative"}


def text_for(wording, order, with_image):
    s0, s1 = (STRATEGIES if order == 0 else STRATEGIES[::-1])
    tpl = (WORDING if with_image else BASELINE)[wording]
    return tpl.format(s0=s0, s1=s1, s0_adj=ADJ[s0], s1_adj=ADJ[s1], problem=PROBLEM)


def build(shape, position, wording, order, images_dir):
    text = text_for(wording, order, shape != "none")
    blocks = [{"type": "text", "text": text}]
    if shape != "none":
        path = os.path.join(images_dir, f"{shape}_red.png")
        if not os.path.exists(path):
            symbols.render(shape, "red", path)
        img = {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                           "data": base64.b64encode(open(path, "rb").read()).decode()}}
        blocks = [img, {"type": "text", "text": text}] if position != "after" else [{"type": "text", "text": text}, img]
    return blocks


def one(args, shape, position, wording, idx, cfg, cwd):
    order = idx % 2
    msg = {"type": "user", "message": {"role": "user", "content": build(shape, position, wording, order, args.images_dir)}}
    cmd = ["claude", "-p", "--model", args.model, "--input-format", "stream-json", "--output-format", "stream-json",
           "--verbose", "--tools", "", "--strict-mcp-config", "--no-session-persistence"]
    if position == "first":
        cmd += ["--system-prompt", MINIMAL_SYSTEM]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, input=json.dumps(msg) + "\n", capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=clean_env(cfg), cwd=cwd, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return {"shape": shape, "position": position, "wording": wording, "idx": idx, "label": "error", "error": "timeout"}
    result, usage, is_error = "", None, None
    for line in r.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result, usage, is_error = ev.get("result") or "", ev.get("usage"), ev.get("is_error")
    label = classify.classify(result) if result and not is_error else "error"
    return {"model": args.model, "shape": shape, "position": position, "wording": wording, "order": order, "idx": idx,
            "label": label, "answer": result, "is_error": is_error, "usage": usage, "seconds": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--shapes", default="none,spiral,branching_arrows,heart")
    ap.add_argument("--positions", default="first,default,after")
    ap.add_argument("--wordings", default="explicit,neutral,ordinary")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--images-dir", default=os.path.join(REPRO, "symbols"))
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, f"samples-e3-{args.model}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            try:
                s = json.loads(line)
                if s.get("label") not in (None, "error"):
                    done.add((s["shape"], s["position"], s["wording"], s["idx"]))
            except json.JSONDecodeError:
                pass
    parent = tempfile.mkdtemp(prefix="e3_")
    cfg = os.path.join(parent, "cfg"); os.makedirs(cfg); open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "cwd"); os.makedirs(cwd)
    jobs = [(sh, po, wo, i) for sh in args.shapes.split(",") for po in args.positions.split(",")
            for wo in args.wordings.split(",") for i in range(args.n) if (sh, po, wo, i) not in done]
    log(f"E3 model={args.model}: {len(jobs)} samples to run ({len(done)} done) -> {out_path}")
    counts = {}
    with open(out_path, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, args, sh, po, wo, i, cfg, cwd) for sh, po, wo, i in jobs]
        for k, f in enumerate(cf.as_completed(futs), start=1):
            s = f.result()
            fh.write(json.dumps(s, ensure_ascii=False) + "\n"); fh.flush()
            key = f"{s['shape']}/{s['position']}/{s['wording']}"
            counts.setdefault(key, {}).setdefault(s["label"], 0)
            counts[key][s["label"]] += 1
            if k % 20 == 0 or k == len(jobs):
                log(f"{k}/{len(jobs)} done")
    for key in sorted(counts):
        log(f"  {key}: {counts[key]}")
    log("finished; summarise with: python summarize_e3.py " + out_path)


if __name__ == "__main__":
    main()
