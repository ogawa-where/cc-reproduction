# cc-reproduction: Reproducing reported Claude Code behaviors, one paper at a time

[![reproductions](https://img.shields.io/badge/reproductions-1-blue)](#reproductions)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.1.310-black?logo=anthropic)](https://code.claude.com)
[![papers](https://img.shields.io/badge/papers-arXiv-b31b1b?logo=arxiv)](https://arxiv.org)

<div align="center" style="font-size: 1.1rem; margin-bottom: 1rem;"><sub>
README: <a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a>
</sub></div>

## Check what the papers say against the real Claude Code

Each reproduction lives in its own directory, named `YYYYMMDD_<citation key>` (the reproduction date, then the authors' initials and year; Xu & Wu, 2026 → `XW26`). Every directory ships a harness, the tasks, and a README that covers the paper's claims, the setup, what was prepared, the procedure, the results and a discussion.

```text
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
```

```text
 ▐▛███▛█   Claude Code v2.1.310
▝▜██████▀  Sonnet 5.5 · Claude API
 ▝▝   ▝▝   ~/cc-reproduction

▎ This repository reproduces behaviors of Claude Code reported in papers, one paper per directory.
▎ Each directory holds the harness, the tasks and the write-up of the result.
```

## Reproductions

| Reproduced on | Paper (published) | Directory | Result |
|:--|:--|:--|:--:|
| 2026-10-26 | [XW26] [Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix](https://arxiv.org/abs/2610.30571) (2026-10-22) | [`20261026_XW26/`](20261026_XW26/) | ✅ reproduced |

```text
● Glob(**/README.md)
  ⎿  Found 1 reproduction

● Open a directory's README for the paper's claims, the setup, the procedure, the results and the discussion.

────────────────────────────────────────────────────────────────────────────────────────────────────
❯ Try "refactor <filepath>"
────────────────────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ auto mode on (shift+tab to cycle)
```
