# cc-reproduction: 論文で報告された Claude Code の挙動を再現し、その先を調べる

[![studies](https://img.shields.io/badge/studies-5-blue)](#再現の一覧)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-v2.1.310-black?logo=anthropic)](https://code.claude.com)
[![papers](https://img.shields.io/badge/papers-arXiv-b31b1b?logo=arxiv)](https://arxiv.org)

<div align="center" style="font-size: 1.1rem; margin-bottom: 1rem;"><sub>
README: <a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a>
</sub></div>

## 論文の報告を実物の Claude Code で確かめ、論文が残した問いを調べる

研究は 1 件 1 ディレクトリで、名前は `YYYYMMDD_<引用キー>`（実施日と、著者の頭文字 + 年。Xu & Wu, 2026 → `XW26`）。再現は論文の実験を Claude Code で追試するもの、拡張（`-ext`）は再現した結果を起点に論文が残した問いを調べるもの。各ディレクトリにハーネスとタスクを置き、README に主張・実験環境・準備したもの・手順・結果・考察をまとめている。

結果欄: `OK` は報告された現象が再現、`Done` は実験は完了したが現行の Claude Code では現象が出ない（理由は README）、`Ext` は拡張研究（独自の発見は README）。

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

▎ このリポジトリは論文で報告された Claude Code の現象を 1 件ずつ再現する場所です。
▎ 論文ごとにディレクトリを切り、再現ハーネス・タスク・結果を置いています。

> 再現の一覧を見せて

● Glob(**/README.md)
  ⎿  Found 5 studies

● これまでの再現は次のとおりです。

  ┌────────────┬───────────────────────────────────┬────────────────────────┬────────┐
  │ Date       │ Paper (published)                 │ Directory              │ Result │
  ├────────────┼───────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-10-26 │ [XW26] <a href="https://arxiv.org/abs/2610.30571">Stale Instruction Files</a>    │ <a href="./20261026_XW26/">20261026_XW26/</a>         │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.30571">Override the Code in Coding</a>       │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.30571">Agents: A One-Sentence Fix</a>        │                        │        │
  │            │ (2026-10-22)                      │                        │        │
  ├────────────┼───────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-10-29 │ [SBBAA26] <a href="https://arxiv.org/abs/2610.31778">Benchmarks Are</a>          │ <a href="./20261029_SBBAA26/">20261029_SBBAA26/</a>      │ Done   │
  │            │ <a href="https://arxiv.org/abs/2610.31778">Surprisingly Compaction-Friendly</a>  │                        │        │
  │            │ (2026-10-22)                      │                        │        │
  ├────────────┼───────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-01 │ [TWWWKL26] <a href="https://arxiv.org/abs/2610.36449">A Heart Means</a>          │ <a href="./20261101_TWWWKL26/">20261101_TWWWKL26/</a>     │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Recursion: Exploring Visual</a>       │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.36449">Meaning and Communication in VLMs</a> │                        │        │
  │            │ (2026-10-27)                      │                        │        │
  ├────────────┼───────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-01 │ [BGC26] <a href="https://arxiv.org/abs/2610.08036">Same Feedback, Different</a>  │ <a href="./20261101_BGC26/">20261101_BGC26/</a>        │ OK     │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Answer: Measuring Run-to-Run</a>      │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Instability in Frontier-Model</a>     │                        │        │
  │            │ <a href="https://arxiv.org/abs/2610.08036">Customer Feedback Analysis</a>        │                        │        │
  │            │ (2026-10-06)                      │                        │        │
  ├────────────┼───────────────────────────────────┼────────────────────────┼────────┤
  │ 2026-11-02 │ [TWWWKL26-ext] Do real images     │ <a href="./20261102_TWWWKL26-ext/">20261102_TWWWKL26-ext/</a> │ Ext    │
  │            │ steer Claude Code silently, and   │                        │        │
  │            │ does one sentence prevent it?     │                        │        │
  │            │ (extension of TWWWKL26)           │                        │        │
  └────────────┴───────────────────────────────────┴────────────────────────┴────────┘

● SBBAA26: 実験は完了。現象は Claude Code 2.1.310 では出ず、原因は圧縮プロンプトの
  変更。詳細はディレクトリの README。

● 各ディレクトリの README に、論文の主張・実験環境・準備したもの・手順・結果・考察を
  まとめています。

──────────────────────────────────────────────────────────────────────────────────────
❯ Try "refactor &lt;filepath&gt;"
──────────────────────────────────────────────────────────────────────────────────────
  ⏵⏵ auto mode on (shift+tab to cycle)
</pre>
