#!/usr/bin/env python3
"""Paper metrics per (model, language) from judged answers, plus the exogenous ranking pooled over languages.

  python summarize.py results/sonnet [results/opus ...] [--langs en,ja,...] [--top 8] [--by-domain]

Own: references to countries where the input language is official (share of all references). NA: answers with no
country. Exogenous: references to other countries. Div: distinct countries. Ent: entropy of the reference
distribution divided by log(Div). Primary: the country the judge read as the answer's main setting.
"""
import argparse
import collections
import json
import math
import os

OWN = {  # countries where the language is an official language
    "en": {"US", "GB", "IN", "CA", "AU", "NZ", "IE", "ZA", "NG", "PH", "SG", "KE", "GH", "JM", "PK", "UG", "TZ",
           "ZW", "ZM", "MW", "BW", "NA", "SL", "LR", "GM", "CM", "RW", "SS", "SD", "FJ", "PG", "MT", "BS", "BB",
           "BZ", "GY", "TT", "LS", "SZ", "MU", "SC", "VU", "WS", "TO", "KI", "SB", "TV", "NR", "PW", "MH", "FM",
           "AG", "DM", "GD", "KN", "LC", "VC", "ER"},
    "ja": {"JP"},
    "zh": {"CN", "TW", "SG", "HK", "MO"},
    "es": {"ES", "MX", "CO", "AR", "PE", "VE", "CL", "EC", "GT", "CU", "BO", "DO", "HN", "PY", "SV", "NI", "CR", "PA",
           "UY", "GQ", "PR"},
    "ar": {"EG", "SA", "DZ", "MA", "IQ", "SD", "SY", "YE", "TN", "JO", "AE", "LB", "LY", "PS", "OM", "KW", "MR", "QA",
           "BH", "DJ", "KM", "TD", "SO", "ER"},
    "sw": {"KE", "TZ", "UG", "RW"},
}
PAPER_COLS = ["JP", "US", "IN", "CN", "FR", "IT", "GB", "DE", "MX", "BR", "RU", "EG"]


def load(d, lang):
    p = os.path.join(d, f"judged-{lang}.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def stats(rows, lang):
    refs = collections.Counter(c for r in rows for c in r["codes"])
    total = sum(refs.values())
    own = sum(v for c, v in refs.items() if c in OWN[lang])
    na = sum(1 for r in rows if not r["codes"])
    div = len(refs)
    h = -sum(v / total * math.log(v / total) for v in refs.values()) if total else 0.0
    ent = h / math.log(div) if div > 1 else 0.0
    exo = collections.Counter({c: v for c, v in refs.items() if c not in OWN[lang]})
    prim = collections.Counter(r.get("primary") or "-" for r in rows)
    prim_own = sum(v for c, v in prim.items() if c in OWN[lang])
    return {"n": len(rows), "refs": total, "own": own, "own_share": own / total if total else 0, "na": na,
            "div": div, "ent": ent, "exo": exo, "prim": prim, "prim_own": prim_own}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--langs", default="en,ja,zh,es,ar,sw")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--by-domain", action="store_true")
    args = ap.parse_args()
    langs = args.langs.split(",")
    for d in args.dirs:
        model = os.path.basename(os.path.normpath(d))
        print(f"\n=== {model}")
        print(f"{'lang':4} {'n':>4} {'refs':>5} {'own':>11} {'NA':>4} {'div':>4} {'ent':>5}  "
              f"{'primary own':>11}  top exogenous (references)            top exogenous primary")
        pooled, pooled_prim = collections.Counter(), collections.Counter()
        for lang in langs:
            rows = load(d, lang)
            if not rows:
                continue
            s = stats(rows, lang)
            pooled += s["exo"]
            pp = collections.Counter({c: v for c, v in s["prim"].items() if c not in OWN[lang] and c != "-"})
            pooled_prim += pp
            top = " ".join(f"{c}:{v}" for c, v in s["exo"].most_common(args.top))
            topp = " ".join(f"{c}:{v}" for c, v in pp.most_common(4))
            print(f"{lang:4} {s['n']:4} {s['refs']:5} {s['own']:5} ({s['own_share']:.2f}) {s['na']:4} {s['div']:4} "
                  f"{s['ent']:.2f}  {s['prim_own']:4} ({s['prim_own'] / s['n']:.2f})  {top:37}  {topp}")
            if args.by_domain:
                for dom in sorted({r["domain"] for r in rows}):
                    sd = stats([r for r in rows if r["domain"] == dom], lang)
                    print(f"     {dom:10} " + " ".join(f"{c}:{v}" for c, v in sd["exo"].most_common(4)))
        print("pooled exogenous references: " + " ".join(f"{c}:{v}" for c, v in pooled.most_common(10)))
        print("  in the paper's 12 columns: " + " ".join(f"{c}:{pooled[c]}" for c in PAPER_COLS))
        print("pooled exogenous primary:    " + " ".join(f"{c}:{v}" for c, v in pooled_prim.most_common(10)))


if __name__ == "__main__":
    main()
