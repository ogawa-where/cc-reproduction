# cc-reproduction: Reproducing reported Claude Code behaviors, then digging deeper

[![studies](https://img.shields.io/badge/studies-5-blue)](#reproductions)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.1.310-black?logo=anthropic)](https://code.claude.com)
[![papers](https://img.shields.io/badge/papers-arXiv-b31b1b?logo=arxiv)](https://arxiv.org)

<div align="center" style="font-size: 1.1rem; margin-bottom: 1rem;"><sub>
README: <a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a>
</sub></div>

## Check what the papers say against the real Claude Code, then look for what they missed

Each study lives in its own directory, named `YYYYMMDD_<citation key>` (the date, then the authors' initials and year; Xu & Wu, 2026 → `XW26`). A reproduction re-runs a paper's experiment on Claude Code. An extension (`-ext`) starts from a reproduced result and asks a question the paper left open. Every directory ships a harness, the tasks, and a README that covers the claims, the setup, what was prepared, the procedure, the results and a discussion.

Result column: `OK` the reported effect reproduced; `Done` the experiment ran but the effect is absent in current Claude Code (the README says why); `Ext` an extension study with its own findings.

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
  ⎿  Found 5 studies

● Here are the reproductions so far:

  ┌────────────┬─────────────────────────────────────┬────────────────────────┬────────┐
  │ Date       │ Paper (published)                   │ Directory              │ Result │
  ├────────────┼─────────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-10-26 │ [XW26] <a href="https://arxiv.org/abs/2610.30571">Stale Instruction Files</a>      │ <a href="./20261026_XW26/">20261026_XW26/</a>         │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.30571">Override the Code in Coding Agents:</a> │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.30571">A One-Sentence Fix</a>                  │                        │        │
  │            │ (2026-10-22)                        │                        │        │
  ├────────────┼─────────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-10-29 │ [SBBAA26] <a href="https://arxiv.org/abs/2610.31778">Benchmarks Are</a>            │ <a href="./20261029_SBBAA26/">20261029_SBBAA26/</a>      │ Done   │
  │            │ <a href="https://arxiv.org/abs/2610.31778">Surprisingly Compaction-Friendly</a>    │                        │        │
  │            │ (2026-10-22)                        │                        │        │
  ├────────────┼─────────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-01 │ [TWWWKL26] <a href="https://arxiv.org/abs/2610.36449">A Heart Means Recursion:</a> │ <a href="./20261101_TWWWKL26/">20261101_TWWWKL26/</a>     │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Exploring Visual Meaning and</a>        │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Communication in VLMs</a>               │                        │        │
  │            │ (2026-10-27)                        │                        │        │
  ├────────────┼─────────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-01 │ [BGC26] <a href="https://arxiv.org/abs/2610.08036">Same Feedback, Different</a>    │ <a href="./20261101_BGC26/">20261101_BGC26/</a>        │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Answer: Measuring Run-to-Run</a>        │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Instability in Frontier-Model</a>       │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Customer Feedback Analysis</a>          │                        │        │
  │            │ (2026-10-06)                        │                        │        │
  ├────────────┼─────────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-02 │ [TWWWKL26-ext] Do real images steer │ <a href="./20261102_TWWWKL26-ext/">20261102_TWWWKL26-ext/</a> │ Ext    │
  │            │ Claude Code silently, and does one  │                        │        │
  │            │ sentence prevent it? (extension of  │                        │        │
  │            │ TWWWKL26)                           │                        │        │
  └────────────┴─────────────────────────────────────┴────────────────────────┴────────┘

● SBBAA26: the experiment ran; the effect is absent in Claude Code 2.1.310, whose
  compaction prompt changed after the paper's data was collected. See its README.

● Each directory's README covers the paper's claims, the setup, what was prepared,
  the procedure, the results and a discussion.

──────────────────────────────────────────────────────────────────────────────────────
❯ Try "refactor &lt;filepath&gt;"
──────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ auto mode on (shift+tab to cycle)
</pre>
