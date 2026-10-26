# cc-reproduction: 論文で報告された Claude Code の挙動を 1 件ずつ再現する

[![reproductions](https://img.shields.io/badge/reproductions-1-blue)](#再現の一覧)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.1.310-black?logo=anthropic)](https://code.claude.com)
[![papers](https://img.shields.io/badge/papers-arXiv-b31b1b?logo=arxiv)](https://arxiv.org)

<div align="center" style="font-size: 1.1rem; margin-bottom: 1rem;"><sub>
README: <a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a>
</sub></div>

## 論文の報告を、実物の Claude Code で確かめる

再現は論文ごとに 1 ディレクトリで、名前は `YYYYMMDD_<引用キー>`（再現日と、著者の頭文字 + 年。Xu & Wu, 2026 → `XW26`）。各ディレクトリに再現ハーネスとタスクを置き、README に論文の主張・実験環境・準備したもの・手順・結果・考察をまとめている。

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

▎ このリポジトリは、論文で報告された Claude Code の現象を 1 件ずつ再現する場所です。
▎ 論文ごとにディレクトリを切り、再現ハーネス・タスク・結果を置いています。

> 再現の一覧を見せて

● Glob(**/README.md)
  ⎿  Found 1 reproduction

● これまでの再現は次のとおりです。

  ┌───────────────┬─────────────────────────────────────┬────────────────┬────────┐
  │ Reproduced on │ Paper (published)                   │ Directory      │ Result │
  ├───────────────┼─────────────────────────────────────┼────────────────┼────────┤
  │ 2026-10-26    │ [XW26] <a href="https://arxiv.org/abs/2610.30571">Stale Instruction Files</a>      │ <a href="./20261026_XW26/">20261026_XW26/</a> │ OK     │
  │               │ <a href="https://arxiv.org/abs/2610.30571">Override the Code in Coding Agents:</a> │                │        │
  │               │ <a href="https://arxiv.org/abs/2610.30571">A One-Sentence Fix</a>                  │                │        │
  │               │ (2026-10-22)                        │                │        │
  └───────────────┴─────────────────────────────────────┴────────────────┴────────┘

● 各ディレクトリの README に、論文の主張・実験環境・準備したもの・手順・結果・考察を
  まとめています。

──────────────────────────────────────────────────────────────────────────────────────
❯ Try "refactor &lt;filepath&gt;"
──────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ auto mode on (shift+tab to cycle)
</pre>
