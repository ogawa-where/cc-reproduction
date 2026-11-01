#!/usr/bin/env python3
"""Generate a frozen, realistic customer-feedback corpus with Claude (once), standing in for the paper's
anonymized multilingual enterprise support feedback. The output file is committed and never regenerated.
Usage: python make_corpus.py --n 300 --out corpus/feedback-300.json"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import claude_call, clean_env, log  # noqa: E402

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["records"],
          "properties": {"records": {"type": "array", "items": {"type": "string"}}}}
SYSTEM = ("You write realistic customer feedback for a fictional mobile banking app (accounts, cards, transfers, bill "
          "pay, budgeting, support chat, statements). Write like real customers: varied length (5 to 80 words), varied "
          "tone, typos now and then, concrete details, sometimes two or three different problems in one message, "
          "sometimes vague, sometimes praise or a feature wish mixed with a complaint. Do not number the records, do not "
          "repeat wording across records, do not mention real companies.")
FOCUS = [
    "mostly login, authentication, verification codes, biometrics, session timeouts",
    "mostly crashes, freezes, slow loading, update regressions on Android and iOS",
    "mostly transfers, payments, pending or delayed transactions, scheduled payments",
    "mostly fees, unexpected charges, exchange rates, refunds, double charges",
    "mostly customer support experience: chat, phone, tickets, bots, response time",
    "mostly notifications, alerts, statements, exports, accounting integrations",
    "mostly cards: activation, declines abroad, virtual cards, wallets, freezing",
    "mostly security worries, phishing, trusted devices, data privacy",
    "mostly UI, navigation, dark mode, accessibility, onboarding",
    "mostly feature requests: budgeting, joint accounts, widgets, multi-currency, savings",
    "a mix of everything above, including praise",
    "a mix of everything above, about a third of the messages written in Japanese and a few in Spanish or German",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus", "feedback-300.json"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    parent = tempfile.mkdtemp(prefix="corpus_")
    cfg = os.path.join(parent, "cfg"); os.makedirs(cfg); open(os.path.join(cfg, "CLAUDE.md"), "w").close()
    cwd = os.path.join(parent, "cwd"); os.makedirs(cwd)
    env = clean_env(cfg)
    per = 25
    texts = []
    k = 0
    while len(texts) < args.n:
        focus = FOCUS[k % len(FOCUS)]
        user = f"Write {per} distinct feedback messages. Focus for this batch: {focus}. Return them as a JSON array of strings."
        obj, meta = claude_call(args.model, SYSTEM, user, SCHEMA, env, cwd)
        k += 1
        if not obj:
            log(f"batch {k} failed: {meta}")
            continue
        new = [t.strip() for t in obj["records"] if isinstance(t, str) and t.strip()]
        texts += new
        log(f"batch {k} ({focus[:40]}...): +{len(new)} -> {len(texts)}")
    rnd = random.Random(args.seed)
    rnd.shuffle(texts)
    texts = texts[:args.n]
    t0 = dt.datetime(2026, 4, 1, 15, 16, 43)
    records = [{"id": i + 1, "alias": f"R{i + 1:04d}", "timestamp": (t0 + dt.timedelta(minutes=37 * i + rnd.randint(0, 30))).isoformat(),
                "text": t} for i, t in enumerate(texts)]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump({"generated": dt.datetime.now().isoformat(timespec="seconds"), "model": args.model, "n": len(records),
               "records": records}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"wrote {len(records)} records -> {args.out}")


if __name__ == "__main__":
    main()
