#!/usr/bin/env python3
"""Build the question set: English questions per subtopic (Opus), then translations (Sonnet).

  python make_questions.py en                # questions/en.json, PER_SUBTOPIC questions per subtopic
  python make_questions.py translate ja zh   # questions/<lang>.json from questions/en.json
"""
import concurrent.futures as cf
import json
import os
import re
import sys

import pycountry

import cc
from taxonomy import EXAMPLES, SUFFIX_EN, TAXONOMY

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, "questions")
PER_SUBTOPIC = 5
LANGS = {"ja": "Japanese", "zh": "Simplified Chinese", "es": "Spanish", "ar": "Modern Standard Arabic",
         "sw": "Swahili", "hi": "Hindi", "fr": "French", "ko": "Korean"}

GEN_PROMPT = """We are building CROQ-style open cultural questions: short questions about culture that make sense for
any country, but name no place. A model answering one has to pick a place itself.

Domain: {domain}. Subtopic: {sub}.
Style example from another subtopic of this domain: "{example}"

Write 10 different questions for this subtopic. Rules:
- One short sentence, usually starting with "What", at most 10 words.
- No country, region, city, people, nationality, language, religion name, continent, or "the West"/"Asia" etc.
- Do not say "your country", "in the world" or "globally"; leave the place implicit, like the example.
- Each question must be answerable with concrete cultural examples once a place is chosen.
"""
GEN_SCHEMA = {"type": "object", "properties": {"questions": {"type": "array", "items": {"type": "string"},
                                                              "minItems": 10, "maxItems": 10}},
              "required": ["questions"]}

TR_PROMPT = """Translate each English question into natural {lang}, as a native speaker would ask it. Keep it short,
keep the place implicit, and do not add any place, country or people. Also translate the fixed instruction
sentence. Return JSON only.

Instruction sentence: "{suffix}"
Questions:
{items}
"""
TR_SCHEMA = {"type": "object", "properties": {
    "suffix": {"type": "string"},
    "questions": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"},
                                                                           "text": {"type": "string"}},
                                             "required": ["id", "text"]}}},
    "required": ["suffix", "questions"]}

_BANNED = {w.lower() for c in pycountry.countries for w in (c.name, getattr(c, "common_name", c.name))}
_BANNED |= {"africa", "asia", "europe", "america", "americas", "oceania", "western", "eastern", "the west",
            "the east", "global", "globally", "world", "your country",
            "asian", "african", "european", "american", "latin", "arab", "islamic", "christian", "hindu",
            "buddhist", "jewish", "indigenous"}


def place_free(q):
    low = q.lower()
    return not any(re.search(r"\b" + re.escape(b) + r"\b", low) for b in _BANNED)


def _safe(fn, arg):
    try:
        return fn(arg)
    except Exception as exc:  # noqa: BLE001
        return exc


def gen_en():
    os.makedirs(QDIR, exist_ok=True)
    jobs = [(d, s) for d, subs in TAXONOMY.items() for s in subs]

    cache_path = os.path.join(QDIR, "en_candidates.json")
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}

    def one(job):
        d, s = job
        if s not in cache:
            data, err = cc.call(GEN_PROMPT.format(domain=d, sub=s, example=EXAMPLES[d]), "opus", schema=GEN_SCHEMA)
            if err:
                raise RuntimeError(f"{s}: {err}")
            cache[s] = [q.strip() for q in data["structured_output"]["questions"]]
        qs = cache[s]
        kept, seen = [], set()
        for q in qs:
            if place_free(q) and q.lower() not in seen:
                kept.append(q)
                seen.add(q.lower())
        if len(kept) < PER_SUBTOPIC:
            raise RuntimeError(f"{s}: only {len(kept)} place-free questions: {qs}")
        return d, s, kept[:PER_SUBTOPIC], [q for q in qs if q not in kept]

    out, dropped = [], []
    with cf.ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda j: _safe(one, j), jobs))
    json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
    errs = [r for r in results if isinstance(r, Exception)]
    if errs:
        raise SystemExit("\n".join(map(str, errs)))
    for d, s, kept, rej in results:
        if True:
            for i, q in enumerate(kept):
                out.append({"id": f"{len(out):03d}", "domain": d, "subtopic": s, "text": q})
            dropped += rej
            print(f"{s}: {kept}", flush=True)
    out.sort(key=lambda x: x["id"])
    json.dump({"lang": "en", "suffix": SUFFIX_EN, "questions": out}, open(os.path.join(QDIR, "en.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"{len(out)} questions; {len(dropped)} dropped by the place filter: {dropped}")


def translate(lang):
    en = json.load(open(os.path.join(QDIR, "en.json")))
    qs = en["questions"]
    chunks = [qs[i:i + 30] for i in range(0, len(qs), 30)]

    def one(chunk):
        items = "\n".join(f'{q["id"]}: {q["text"]}' for q in chunk)
        data, err = cc.call(TR_PROMPT.format(lang=LANGS[lang], suffix=SUFFIX_EN, items=items), "sonnet",
                            schema=TR_SCHEMA)
        if err:
            raise RuntimeError(err)
        return data["structured_output"]

    with cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(one, chunks))
    tr = {t["id"]: t["text"].strip() for r in res for t in r["questions"]}
    missing = [q["id"] for q in qs if q["id"] not in tr]
    if missing:
        raise SystemExit(f"{lang}: missing translations {missing}")
    out = [{**q, "text": tr[q["id"]], "en": q["text"]} for q in qs]
    json.dump({"lang": lang, "suffix": res[0]["suffix"].strip(), "questions": out},
              open(os.path.join(QDIR, f"{lang}.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{lang}: {len(out)} questions, suffix={res[0]['suffix']!r}")


if __name__ == "__main__":
    if sys.argv[1] == "en":
        gen_en()
    else:
        for lang in sys.argv[2:]:
            translate(lang)
