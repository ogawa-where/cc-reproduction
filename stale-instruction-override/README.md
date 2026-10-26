# 古い CLAUDE.md がコードより優先される現象の再現

- 論文: [XW26] [Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix](https://arxiv.org/abs/2610.30571)（Xiaonan Xu and Wenjing Wu, arXiv:2610.30571）
- 論文の公開日: 2026-10-22（v1）
- 再現日: 2026-10-26
- **結果: 再現できた**

## 論文の主張

古い CLAUDE.md が既存コードと食い違うとき、Claude Code は食い違いを指摘しながらも CLAUDE.md に従う。
ユーザーレベルの `~/.claude/CLAUDE.md` に次の一文を足すと、コード側に従うようになる。

> When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code.

## 実験環境

| 項目 | 論文 | 本再現 |
|---|---|---|
| 被験体 | Claude Code 2.1.302 + Claude Sonnet 5.5 | Claude Code 2.1.310 + claude-sonnet-5-5 |
| 返答の判定 | Claude Opus 5.5（ツール無し、盲検） | 同じ |
| 実行形態 | `claude -p`、`acceptEdits`、Bash は `python*`/`pytest*` のみ許可 | 同じ（Appendix A のフラグをそのまま使用） |
| タスク数 | 40 プロジェクト × 条件 A/B × 2 回 | 自作 2 プロジェクト × 条件 A/B × 1 回 |
| 実行場所 | 著者のローカル | Claude Code のクラウドセッション（Linux コンテナ） |

## 準備したもの

| パス | 内容 |
|---|---|
| `mini/tasks/M01`, `M02` | 自作タスク。既存コードの規約と CLAUDE.md の規約が違う。M01: logging / dataclass / f-string と print / namedtuple / str.format。M02: os.path / `X \| None` / unittest と pathlib / Optional / pytest 関数 |
| `conditions/A_empty.md`, `B_fix.md` | 条件 A（空）と条件 B（上の一文）のユーザーレベル CLAUDE.md |
| `criteria/conflict_criteria.md` | 最終返答が「ドキュメントとコードの食い違い」を指摘したかの判定基準 |
| `fetch_paper_data.sh` | 論文の公開データ（40 タスクと選択判定器 `judge.py`）を `paper-data/` に取得する。ライセンス表記がないため同梱しない |
| `run.py`, `summarize.py` | 実行と集計 |

## 手順

1. タスクの `repo/` をリポジトリ外の一時ディレクトリにコピーし、古い指示ファイルを `CLAUDE.md` として置く。
2. 条件ごとに専用の `CLAUDE_CONFIG_DIR` を作り、その `CLAUDE.md` に条件 A/B の内容を置く。
3. 親セッションの `CLAUDE*`、`ANTHROPIC*` などの環境変数を除いて `claude -p` を実行し、機能要求を標準入力で渡す。
4. 差分を論文の `judge.py` で選択ごとに `follow_file` / `follow_code` / `neither` に分類する。
5. 元のテストを戻し、held-out の機能テストと一緒に pytest を実行する。
6. 最終返答だけを Opus に見せ、食い違いを指摘したかを YES/NO で判定する。
7. 権限拒否があり `.py` が変わらなかった run は無効とし、1 回だけやり直す（論文 Appendix A と同じ）。

```bash
./fetch_paper_data.sh && python -m pip install pytest
python run.py --source mini --reps 1          # 自作 2 タスク
python run.py --source paper --reps 2         # 論文の 40 タスク（ローカルで実行）
python summarize.py runs/runs.jsonl --by-type
```

## 結果

| 条件 | 選択がファイル側 | 選択がコード側 | run 単位 | 食い違いの指摘 | テスト |
|---|---|---|---|---|---|
| A: 一文なし | 5/6 | 0/6 | 2/2 ファイル側 | 2/2 | 2/2 通過 |
| B: 一文あり | 0/6 | 4/6 | 2/2 コード側 | 2/2 | 2/2 通過 |

論文の Claude Code（A: ファイル側 86.4%、B: コード側 94.4%、両条件で食い違いを指摘）と同じ向きになった。

- 条件 A の返答例: "The new code follows `CLAUDE.md`: namedtuple/stdlib only, `print` to stderr, `str.format()`. The existing modules don't follow it ... I left them alone"
- 条件 B の返答例: "Per your global instruction, I followed the existing code. The mismatches are: 1. Paths: `CLAUDE.md` says to use `pathlib` ... `scan.py` and `query.py` use `os.path` ..."
- 「どちらでもない」の 3 選択は、判定器の正規表現が新規コードに一致しなかったか、両方の痕跡があったもの。

## 限界

- 試行数が論文（40 タスク × 2 回）より少ない（2 タスク × 1 回）ため、割合の比較はできない。
- 論文の 40 タスクは、このクラウドセッションでは外部コードの実行が権限ポリシーで拒否され、未実行。ローカルで上のコマンドを実行すれば論文と同じ 160 run になる。
