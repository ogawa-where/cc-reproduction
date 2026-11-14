#!/usr/bin/env python3
"""Regenerate the terminal-style <pre> block (study tables) in README.md and README_ja.md.

The study list lives here; run `python scripts/readme_tables.py --write` after adding a study.
Every line of the block stays within 86 columns so GitHub does not clip it. Cells use only ASCII
inside the box so the borders line up in browser monospace fonts."""
from __future__ import annotations

import argparse
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPRODUCTIONS = [  # date, citation key, title lines (each <= 33 chars), arXiv id, published, directory, result
    ("2026-10-26", "XW26", ["Stale Instruction Files", "Override the Code in Coding", "Agents: A One-Sentence Fix"],
     "2610.30571", "2026-10-22", "20261026_XW26", "OK"),
    ("2026-10-29", "SBBAA26", ["Benchmarks Are", "Surprisingly Compaction-Friendly"],
     "2610.31778", "2026-10-22", "20261029_SBBAA26", "Done"),
    ("2026-11-01", "TWWWKL26", ["A Heart Means", "Recursion: Exploring Visual", "Meaning and Communication in VLMs"],
     "2610.36449", "2026-10-27", "20261101_TWWWKL26", "OK"),
    ("2026-11-01", "BGC26", ["Same Feedback, Different", "Answer: Measuring Run-to-Run", "Instability in Frontier-Model",
                             "Customer Feedback Analysis"], "2610.08036", "2026-10-06", "20261101_BGC26", "OK"),
    ("2026-11-02", "B26", ["Thinking-in-Bets at Test Time", "Reduces Sycophantic Revisions", "in LLM Agents"],
     "2610.34654", "2026-10-26", "20261102_B26", "OK"),
    ("2026-11-12", "FPC26", ["Why are all LLMs Obsessed", "with Japanese Culture? On the",
                             "Hidden Cultural and Regional", "Biases of LLMs"],
     "2604.21751", "2026-04-23", "20261112_FPC26", "OK"),
]
EXTENSIONS = [  # date, question lines (each <= 31 chars), based-on key, directory, finding lines (en, ja)
    ("2026-11-02", ["Do real images steer Claude", "Code silently, and does one", "sentence prevent it?"],
     "TWWWKL26", "20261102_TWWWKL26-ext",
     ["● TWWWKL26-ext: no silent steering. It happens only when the request lets the image",
      "  decide, and one sentence in CLAUDE.md prevents it. Details in its README."],
     ["● TWWWKL26-ext: 黙った誘導は無し。依頼文が画像に決定権を与えたときだけ起き、",
      "  CLAUDE.md の一文で防げる。詳細はディレクトリの README。"]),
    ("2026-11-12", ["Which Claude models pick Japan", "most for open cultural", "questions?"],
     "FPC26", "20261112_FPC26-ext",
     ["● FPC26-ext: all 11 Claude models put Japan first in English. Opus 4.7 picks it most",
      "  (16%), Haiku 5.5 least (7%); newer Sonnet and Opus pick it more often."],
     ["● FPC26-ext: 英語では 11 モデルすべてで日本が首位。最多は Opus 4.7（16%）、",
      "  最少は Haiku 5.5（7%）。Sonnet と Opus は新しい世代ほど日本を選ぶ。"]),
]


def link(t, h):
    return f'<a href="{h}">{t}</a>'


def w(t):
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in re.sub(r"<[^>]+>", "", t))


def table(header, rows, indent="  "):
    def cells(row):
        return [c if isinstance(c, list) else [c] for c in row]
    widths = [max([w(header[i])] + [w(l) for row in rows for l in cells(row)[i]]) for i in range(len(header))]
    top = "┌" + "┬".join("─" * (x + 2) for x in widths) + "┐"
    mid = "├" + "┼".join("─" * (x + 2) for x in widths) + "┤"
    bot = "└" + "┴".join("─" * (x + 2) for x in widths) + "┘"

    def line(v):
        return "│" + "│".join(" " + x + " " * (widths[i] - w(x)) + " " for i, x in enumerate(v)) + "│"
    out = [top, line(header), mid]
    for k, row in enumerate(rows):
        if k:
            out.append(mid)
        cs = cells(row)
        n = max(len(c) for c in cs)
        for j in range(n):
            out.append(line([c[j] if j < len(c) else "" for c in cs]))
    out.append(bot)
    return "\n".join(indent + l for l in out)


def repro_table():
    rows = []
    for date, key, title, arx, pub, d, res in REPRODUCTIONS:
        url = f"https://arxiv.org/abs/{arx}"
        lines = [f"[{key}] " + link(title[0], url)] + [link(t, url) for t in title[1:]] + [f"({pub})"]
        rows.append([date, lines, link(d + "/", f"./{d}/"), res])
    return table(["Date", "Paper (published)", "Directory", "Result"], rows)


def ext_table():
    rows = [[date, q, base, link(d + "/", f"./{d}/")] for date, q, base, d, _, _ in EXTENSIONS]
    return table(["Date", "Question", "Based on", "Directory"], rows)


def block(lang):
    splash = open(os.path.join(ROOT, "scripts", "splash.txt"), encoding="utf-8").read().rstrip("\n")
    rule = "─" * 86
    if lang == "en":
        notice = ["▎ This repository reproduces behaviors of Claude Code reported in papers and then",
                  "▎ extends them: one study per directory, with the harness, the tasks and the write-up."]
        q1, q2 = "> Show me the reproductions", "> And the extension studies"
        a1 = ["● Glob(**/README.md)", f"  ⎿  Found {len(REPRODUCTIONS) + len(EXTENSIONS)} studies", "",
              "● Reproductions so far (OK: the reported effect reproduced; Done: the experiment ran,",
              "  but the effect is absent in current Claude Code, see the README):", ""]
        a2 = ["● Extension studies start from a reproduced result and ask a question the paper left",
              "  open; what they found is summarised under the table:", ""]
        findings = [f for *_, en, _ in EXTENSIONS for f in en]
        tail = ["● Each directory's README covers the claims, the setup, what was prepared, the",
                "  procedure, the results and a discussion."]
    else:
        notice = ["▎ このリポジトリは、論文で報告された Claude Code の現象を再現し、その先を調べます。",
                  "▎ 研究ごとにディレクトリを切り、ハーネス・タスク・結果を置いています。"]
        q1, q2 = "> 再現の一覧を見せて", "> 拡張研究の一覧も"
        a1 = ["● Glob(**/README.md)", f"  ⎿  Found {len(REPRODUCTIONS) + len(EXTENSIONS)} studies", "",
              "● これまでの再現です（OK: 報告された現象が再現、Done: 実験は完了したが現行の",
              "  Claude Code では現象が出ない。理由は README）。", ""]
        a2 = ["● 拡張研究は、再現した結果を起点に論文が残した問いを調べるものです。", "  何が分かったかは表の下に要約しています。", ""]
        findings = [f for *_, ja in EXTENSIONS for f in ja]
        tail = ["● 各ディレクトリの README に、主張・実験環境・準備したもの・手順・結果・考察を", "  まとめています。"]
    lines = [splash, "", " ▐▛███▛█   Claude Code v2.1.310", "▝▜██████▀  Sonnet 5.5 · Claude API", " ▝▝   ▝▝   ~/cc-reproduction", "",
             *notice, "", q1, "", *a1, repro_table(), "", q2, "", *a2, ext_table(), "", *findings, "", *tail, "",
             rule, '❯ Try "refactor &lt;filepath&gt;"', rule, "  ⏵⏵ auto mode on (shift+tab to cycle)"]
    return "<pre>\n" + "\n".join(lines) + "\n</pre>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    for path, lang in (("README.md", "en"), ("README_ja.md", "ja")):
        p = os.path.join(ROOT, path)
        s = open(p, encoding="utf-8").read()
        i, j = s.index("<pre>"), s.index("</pre>") + len("</pre>")
        new = block(lang)
        width = max(w(l) for l in new.splitlines())
        print(f"{path}: pre block {len(new.splitlines())} lines, max width {width}" + ("  (over 86!)" if width > 86 else ""))
        if args.write:
            open(p, "w", encoding="utf-8").write(s[:i] + new + s[j:])


if __name__ == "__main__":
    main()
