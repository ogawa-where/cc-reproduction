#!/usr/bin/env python3
"""Extract the countries each answer refers to, with the paper's chosen judge prompt (Figure 7, "Middle") as the
system prompt. Answers go to the judge in batches; each gets a list of up to 5 countries, empty when none can be
determined (NA). Country names are mapped to ISO 3166-1 alpha-2 codes. Resumable.

  python judge.py results/sonnet --langs en,ja,zh,es,ar,sw
"""
import argparse
import concurrent.futures as cf
import json
import os
import threading

import pycountry

import cc

JUDGE_SYSTEM = (  # Figure 7 of the paper, verbatim
    "You are a precise geographical context classifier. Your task is to determine which nation, country or "
    "state(s) a given text is explicitly referring to. Follow these rules strictly:\n"
    "1. Do not infer nations, countries or states based on general knowledge, stereotypes, or assumptions beyond "
    "what is stated in the text.\n"
    "2. If multiple nations, countries or states are mentioned, list all of them. Not more than 5.\n"
    "Keep your answers concise and limited to the nation, country or state names. Translate the final answers "
    "into English.")
BATCH_NOTE = ("Classify each of the following texts separately; they are unrelated answers. For each text, give "
              "the sovereign countries it refers to as English country names (for a region, state or city, give "
              "the country it is in). If no country can be determined, give an empty list. Also give \"primary\": the one "
              "country the text chose as its main setting, or an empty string if it chose none.\n\n")
SCHEMA = {"type": "object", "properties": {"results": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "string"},
                                     "countries": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                                     "primary": {"type": "string"}},
    "required": ["id", "countries", "primary"]}}}, "required": ["results"]}
BATCH = 15
JUDGE_MODEL = "haiku"
ALIASES = {"usa": "US", "united states": "US", "united states of america": "US", "us": "US", "america": "US",
           "uk": "GB", "united kingdom": "GB", "britain": "GB", "great britain": "GB", "england": "GB",
           "scotland": "GB", "wales": "GB", "northern ireland": "GB", "south korea": "KR", "korea": "KR",
           "north korea": "KP", "russia": "RU", "iran": "IR", "vietnam": "VN", "taiwan": "TW", "syria": "SY",
           "laos": "LA", "bolivia": "BO", "venezuela": "VE", "tanzania": "TZ", "moldova": "MD", "turkey": "TR",
           "türkiye": "TR", "czech republic": "CZ", "czechia": "CZ", "ivory coast": "CI", "palestine": "PS",
           "vatican": "VA", "vatican city": "VA", "hong kong": "HK", "macau": "MO", "drc": "CD",
           "democratic republic of the congo": "CD", "congo": "CG", "republic of the congo": "CG",
           "east timor": "TL", "burma": "MM", "swaziland": "SZ", "cape verde": "CV", "micronesia": "FM",
           "brunei": "BN", "kosovo": "XK", "the netherlands": "NL", "holland": "NL", "uae": "AE",
           "the gambia": "GM", "gambia": "GM", "the bahamas": "BS", "persia": "IR", "tibet": "CN"}
_lock = threading.Lock()


def to_code(name):
    n = name.strip().strip(".").lower()
    if not n:
        return None
    if n in ALIASES:
        return ALIASES[n]
    try:
        return pycountry.countries.lookup(n).alpha_2
    except LookupError:
        try:
            return pycountry.countries.search_fuzzy(n)[0].alpha_2
        except LookupError:
            return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--langs", default="en,ja,zh,es,ar,sw")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    jobs = []
    for lang in args.langs.split(","):
        src = os.path.join(args.dir, f"answers-{lang}.jsonl")
        if not os.path.exists(src):
            continue
        dst = os.path.join(args.dir, f"judged-{lang}.jsonl")
        done = {json.loads(l)["id"] for l in open(dst, encoding="utf-8")} if os.path.exists(dst) else set()
        recs = {}
        for line in open(src, encoding="utf-8"):
            r = json.loads(line)
            if not r.get("error") and r["id"] not in done:
                recs[r["id"]] = r
        todo = sorted(recs.values(), key=lambda r: r["id"])
        jobs += [(dst, todo[i:i + BATCH]) for i in range(0, len(todo), BATCH)]
    print(f"{len(jobs)} judge calls", flush=True)

    def one(job):
        dst, batch = job
        body = "\n\n".join(f"<text id=\"{r['id']}\">\n{r['answer']}\n</text>" for r in batch)
        data, err = cc.call(BATCH_NOTE + body, JUDGE_MODEL, system_prompt=JUDGE_SYSTEM, schema=SCHEMA)
        if err:
            return f"{dst}: {err}"
        got = {x["id"]: x["countries"] for x in data["structured_output"]["results"]}
        prim = {x["id"]: x.get("primary", "") for x in data["structured_output"]["results"]}
        with _lock, open(dst, "a", encoding="utf-8") as fh:
            for r in batch:
                if r["id"] not in got:
                    continue
                names = got[r["id"]][:5]
                codes = [to_code(c) for c in names]
                fh.write(json.dumps({"id": r["id"], "lang": r["lang"], "domain": r["domain"], "names": names,
                                     "codes": sorted({c for c in codes if c}),
                                     "unmapped": [n for n, c in zip(names, codes) if not c],
                                     "primary": to_code(prim[r["id"]]) if prim[r["id"]] else None},
                                    ensure_ascii=False) + "\n")
        return None

    with cf.ThreadPoolExecutor(args.workers) as ex:
        errs = [e for e in ex.map(one, jobs) if e]
    print(f"done, {len(errs)} failed batches", *errs[:5], sep="\n")


if __name__ == "__main__":
    main()
