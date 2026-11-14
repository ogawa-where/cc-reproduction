# cc-reproduction: Reproducing reported Claude Code behaviors, then digging deeper

[![studies](https://img.shields.io/badge/studies-5-blue)](#reproductions)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.1.310-black?logo=anthropic)](https://code.claude.com)
[![papers](https://img.shields.io/badge/papers-arXiv-b31b1b?logo=arxiv)](https://arxiv.org)

<div align="center" style="font-size: 1.1rem; margin-bottom: 1rem;"><sub>
README: <a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a>
</sub></div>

## Check what the papers say against the real Claude Code, then look for what they missed

Each study lives in its own directory, named `YYYYMMDD_<citation key>` (the date, then the authors' initials and year; Xu & Wu, 2026 → `XW26`). A reproduction re-runs a paper's experiment on Claude Code. An extension (`-ext`) starts from a reproduced result and asks a question the paper left open. Every directory ships a harness, the tasks, and a README that covers the claims, the setup, what was prepared, the procedure, the results and a discussion.

Two tables below: reproductions (Result: `OK` the reported effect reproduced; `Done` the experiment ran but the effect is absent in current Claude Code, the README says why) and extension studies (the question, the reproduction it builds on, and a one-line finding under the table).

<pre>
Welcome to Claude Code v2.1.310
..........................................................

     *                                       █████▓▓░
                                 *         ███▓░     ░░
            ░░░░░░                        ███▓░
    ░░░   ░░░░░░░░░░                      ███▓░
   ░░░░░░░░░░░░░░░░░░░    *                ██▓░░      ▓
                                             ░▓▓███▓▓░
 *                                 ░░░░
                                 ░░░░░░░░
                               ░░░░░░░░░░░░░░░░
       █████████                                        *
      ██▄█████▄██                        *
       █████████      *
.......█ █   █ █..........................................

 ▐▛███▛█   Claude Code v2.1.310
▝▜██████▀  Sonnet 5.5 · Claude API
 ▝▝   ▝▝   ~/cc-reproduction

▎ This repository reproduces behaviors of Claude Code reported in papers and then
▎ extends them: one study per directory, with the harness, the tasks and the write-up.

> Show me the reproductions

● Glob(**/README.md)
  ⎿  Found 8 studies

● Reproductions so far (OK: the reported effect reproduced; Done: the experiment ran,
  but the effect is absent in current Claude Code, see the README):

  ┌────────────┬─────────────────────────────────────┬────────────────────┬────────┐
  │ Date       │ Paper (published)                   │ Directory          │ Result │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-10-26 │ [XW26] <a href="https://arxiv.org/abs/2610.30571">Stale Instruction Files</a>      │ <a href="./20261026_XW26/">20261026_XW26/</a>     │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.30571">Override the Code in Coding</a>         │                    │        │
  │            │ <a href="https://arxiv.org/abs/2610.30571">Agents: A One-Sentence Fix</a>          │                    │        │
  │            │ (2026-10-22)                        │                    │        │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-10-29 │ [SBBAA26] <a href="https://arxiv.org/abs/2610.31778">Benchmarks Are</a>            │ <a href="./20261029_SBBAA26/">20261029_SBBAA26/</a>  │ Done   │
  │            │ <a href="https://arxiv.org/abs/2610.31778">Surprisingly Compaction-Friendly</a>    │                    │        │
  │            │ (2026-10-22)                        │                    │        │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-11-01 │ [TWWWKL26] <a href="https://arxiv.org/abs/2610.36449">A Heart Means</a>            │ <a href="./20261101_TWWWKL26/">20261101_TWWWKL26/</a> │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Recursion: Exploring Visual</a>         │                    │        │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Meaning and Communication in VLMs</a>   │                    │        │
  │            │ (2026-10-27)                        │                    │        │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-11-01 │ [BGC26] <a href="https://arxiv.org/abs/2610.08036">Same Feedback, Different</a>    │ <a href="./20261101_BGC26/">20261101_BGC26/</a>    │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Answer: Measuring Run-to-Run</a>        │                    │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Instability in Frontier-Model</a>       │                    │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Customer Feedback Analysis</a>          │                    │        │
  │            │ (2026-10-06)                        │                    │        │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-11-02 │ [B26] <a href="https://arxiv.org/abs/2610.34654">Thinking-in-Bets at Test Time</a> │ <a href="./20261102_B26/">20261102_B26/</a>      │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.34654">Reduces Sycophantic Revisions</a>       │                    │        │
  │            │ <a href="https://arxiv.org/abs/2610.34654">in LLM Agents</a>                       │                    │        │
  │            │ (2026-10-26)                        │                    │        │
  ├────────────┼─────────────────────────────────────┼────────────────────┼────────┤
  │ 2026-11-12 │ [FPC26] <a href="https://arxiv.org/abs/2604.21751">Why are all LLMs Obsessed</a>   │ <a href="./20261112_FPC26/">20261112_FPC26/</a>    │ OK     │
  │            │ <a href="https://arxiv.org/abs/2604.21751">with Japanese Culture? On the</a>       │                    │        │
  │            │ <a href="https://arxiv.org/abs/2604.21751">Hidden Cultural and Regional</a>        │                    │        │
  │            │ <a href="https://arxiv.org/abs/2604.21751">Biases of LLMs</a>                      │                    │        │
  │            │ (2026-04-23)                        │                    │        │
  └────────────┴─────────────────────────────────────┴────────────────────┴────────┘

> And the extension studies

● Extension studies start from a reproduced result and ask a question the paper left
  open; what they found is summarised under the table:

  ┌────────────┬────────────────────────────────┬──────────┬────────────────────────┐
  │ Date       │ Question                       │ Based on │ Directory              │
  ├────────────┼────────────────────────────────┼──────────┼────────────────────────┤
  │ 2026-11-02 │ Do real images steer Claude    │ TWWWKL26 │ <a href="./20261102_TWWWKL26-ext/">20261102_TWWWKL26-ext/</a> │
  │            │ Code silently, and does one    │          │                        │
  │            │ sentence prevent it?           │          │                        │
  ├────────────┼────────────────────────────────┼──────────┼────────────────────────┤
  │ 2026-11-12 │ Which Claude models pick Japan │ FPC26    │ <a href="./20261112_FPC26-ext/">20261112_FPC26-ext/</a>    │
  │            │ most for open cultural         │          │                        │
  │            │ questions?                     │          │                        │
  └────────────┴────────────────────────────────┴──────────┴────────────────────────┘

● TWWWKL26-ext: no silent steering. It happens only when the request lets the image
  decide, and one sentence in CLAUDE.md prevents it. Details in its README.
● FPC26-ext: all 11 Claude models put Japan first in English. Opus 4.7 picks it most
  (16%), Haiku 5.5 least (7%); newer Sonnet and Opus pick it more often.

● Each directory's README covers the claims, the setup, what was prepared, the
  procedure, the results and a discussion.

──────────────────────────────────────────────────────────────────────────────────────
❯ Try "refactor &lt;filepath&gt;"
──────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ auto mode on (shift+tab to cycle)
</pre>
