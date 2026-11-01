"""Deterministic long pastes (logs) that the scripted user attaches to a turn, to grow the context
the way real sessions do (users paste logs, test output, traces). Each paste hides one issue the
agent is asked to find. Sizes are in KB of text (~4 chars per token)."""
from __future__ import annotations

import random

LEVELS = ["INFO", "INFO", "INFO", "INFO", "DEBUG", "DEBUG", "WARN"]


def _lines(rng, n, fmt):
    out = []
    t = 1_700_000_000 + rng.randint(0, 10_000)
    for i in range(n):
        t += rng.randint(1, 9)
        out.append(fmt(rng, t, i))
    return out


def notes_session_log(seed: int, kb: int) -> str:
    """A sync-service log: many note sync lines, one of which shows a tag stored in upper case."""
    rng = random.Random(seed)
    words = ["todo", "work", "home", "urgent", "idea", "later", "read", "call", "buy", "fix"]

    def fmt(rng, t, i):
        lvl = rng.choice(LEVELS)
        nid = rng.randint(1, 900)
        tag = rng.choice(words)
        return f"{t} {lvl} sync note_id={nid} tags=[{tag}] bytes={rng.randint(40, 900)} host=sync-{rng.randint(1, 4)}"
    n = kb * 1024 // 85
    lines = _lines(rng, n, fmt)
    k = rng.randint(n // 2, n - 10)
    lines[k] = lines[k].replace("tags=[", "tags=[", 1).replace(f"tags=[{lines[k].split('tags=[')[1].split(']')[0]}]", "tags=[Urgent]")
    lines[k + 5] = f"{1_700_000_000} ERROR sync rejected note_id=413 reason=tag-not-lowercase tag=Urgent"
    return "\n".join(lines)


def pipeline_report_log(seed: int, kb: int) -> str:
    """A nightly report job log: per-file lines and one month total that does not add up."""
    rng = random.Random(seed)

    def fmt(rng, t, i):
        lvl = rng.choice(LEVELS)
        return (f"{t} {lvl} report file=sales_2026q3.csv rows={rng.randint(300, 700)} region={rng.choice(['north', 'south', 'east', 'west'])} "
                f"revenue={rng.uniform(100, 99999):.2f} worker={rng.randint(1, 8)}")
    n = kb * 1024 // 100
    lines = _lines(rng, n, fmt)
    k = rng.randint(n // 2, n - 10)
    lines[k] = f"{1_700_000_000} WARN report month=2026-08 total=1234567.891 expected two decimals, got three"
    lines[k + 3] = f"{1_700_000_000} ERROR report checksum mismatch month=2026-08 sum_of_regions!=month_total"
    return "\n".join(lines)


def site_build_log(seed: int, kb: int) -> str:
    """A CI build log for the site: many page lines and one page whose link ends in `.md`."""
    rng = random.Random(seed)
    pages = ["index", "about", "faq", "pricing", "team", "blog-2026-07", "blog-2026-08", "contact", "legal", "status"]

    def fmt(rng, t, i):
        lvl = rng.choice(LEVELS)
        p = rng.choice(pages)
        return f"{t} {lvl} build page={p}.md -> out/{p}.html bytes={rng.randint(200, 9000)} ms={rng.randint(1, 40)}"
    n = kb * 1024 // 80
    lines = _lines(rng, n, fmt)
    k = rng.randint(n // 2, n - 10)
    lines[k] = f"{1_700_000_000} WARN build index link href=./pricing.md (expected pricing.html)"
    lines[k + 2] = f"{1_700_000_000} ERROR build link-check 1 broken link in out/index.html"
    return "\n".join(lines)


GENERATORS = {"notes_session_log": notes_session_log, "pipeline_report_log": pipeline_report_log,
              "site_build_log": site_build_log}


def make(kind: str, seed: int, kb: int) -> str:
    return GENERATORS[kind](seed, kb)
