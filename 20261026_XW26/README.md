# 古い CLAUDE.md がコードより優先される現象の再現

- 論文: [XW26] [Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix](https://arxiv.org/abs/2610.30571)（Xiaonan Xu and Wenjing Wu, arXiv:2610.30571）
- 論文の公開日: 2026-10-22（v1）
- 再現日: 2026-10-26

> [!IMPORTANT]
> **再現できた。** 一文なしでは 2/2 run が古い CLAUDE.md に従い、一文ありでは 2/2 run が既存コード側に反転した。どの run も食い違いを指摘した。

## 論文の主張

**背景.** コーディングエージェントは作業の前にプロジェクトの指示ファイル（Claude Code は CLAUDE.md、Codex CLI は AGENTS.md）を読む。指示ファイルは一度書かれると更新されにくく、コードの方が先に変わる。たとえばコードを print から logging に移したあとも、CLAUDE.md に「進捗は print() で出す」という行が残る。この状態では、エージェントは同じ規約について食い違う 2 つの説明を受け取る。

**観察した現象.** 著者らは、指示ファイルが片方の規約を要求し、既存コードが一貫して他方を使う Python プロジェクトを 40 個作り、Claude Code（Sonnet 5.5）と Codex CLI（GPT-6 Sol）に機能追加をさせた（規約の種類は 16、計 320 run）。一文なしの条件では、選択の <mark>90.1% が古い指示ファイル側</mark>だった。

- Claude Code は <mark>80 run 中 79 run で食い違いを指摘した上で、新規コードを CLAUDE.md に合わせた</mark>。食い違いに気づいても、コードの方を「規約違反」として扱った。
- Codex CLI は 80 run 中 20 run で、既存コードを AGENTS.md に合わせて書き換えた。そのうち 17 run で、元のテストが通らなくなった。

**原因の説明.** 指示ファイルは、エージェントのソフトウェアが「指示」（ユーザーメッセージ）としてモデルに渡す。Claude Code はさらに「これらの指示は既定の動作を上書きする。必ず従え」という前置きを付ける。一方、既存コードはエージェントがファイルを開いたときの「ツール出力」としてしか渡らない。モデルは instruction hierarchy の訓練により、プロンプトインジェクション対策として、<mark>指示をツール出力より優先する</mark>。そのため、古くなった記述でも指示の側にある限りコードに勝つ。

**提案する修正.** ユーザーレベルの指示ファイル（`~/.claude/CLAUDE.md` や `~/.codex/AGENTS.md`）に次の一文を足す。

> When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code.

この一文も「指示」として渡るので、「コードに従う」こと自体が指示になり、指示同士の比較になる。一文を足した条件では、コード側に従う選択が <mark>4.2% から 91.4%</mark> に上がり（Claude Code は 7.5% から 94.4%）、既存コードの書き換えはなくなり、テスト通過率は 89.4% から 100% になった。両エージェントとも全 160 run で食い違いを報告した。古い行を探して直す必要がなく、ユーザーが今日から使える。

**提言.** ユーザーはこの一文を自分の指示ファイルに足す。チームはエージェントが報告した食い違いを使って指示ファイルを直す。エージェントの開発元は同じ規則をシステムプロンプトに入れる。モデルの開発元はコードの「記述」を実際のコードと照合するようにモデルを訓練する。

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
| A: 一文なし | 5/6 | 0/6 | <mark>2/2 ファイル側</mark> | 2/2 | 2/2 通過 |
| B: 一文あり | 0/6 | 4/6 | <mark>2/2 コード側</mark> | 2/2 | 2/2 通過 |

- 条件 A の返答例: "The new code follows `CLAUDE.md`: namedtuple/stdlib only, `print` to stderr, `str.format()`. The existing modules don't follow it ... I left them alone"
- 条件 B の返答例: "Per your global instruction, I followed the existing code. The mismatches are: 1. Paths: `CLAUDE.md` says to use `pathlib` ... `scan.py` and `query.py` use `os.path` ..."

## 考察

**論文と一致した点.** <mark>論文が Claude Code について報告した 3 点が、すべて同じ向きで出た</mark>。一文なしでは、run 単位で 2/2 がファイル側に従い、どちらの返答も「既存モジュールは CLAUDE.md の規約に反する」と食い違いを指摘した上でファイルに従った（論文: 選択の 86.4% がファイル側、79/80 run で指摘）。一文ありでは、2/2 がコード側に反転し、食い違いを列挙した（論文: 選択の 94.4% がコード側、全 run で指摘）。既存コードの書き換えがどちらの条件にもなく、テストが全 run で通った点も論文の Claude Code と同じである。

**「どちらでもない」の 3 選択.** 現象の反例ではない。判定器は正規表現で新規コードを見るため、M01 条件 A の REC は結果を dict で返して記録型を作らなかったので「不在」、M01 条件 B の LOG は logging を使いつつ usage 表示に print を 1 回使ったので「混在」、M02 条件 B の PATH は新規コードにパス操作がなかったので「不在」になった。返答の本文では、いずれの run も自分がどちらの規約に従ったかを明記している。

**ハーネス側で観察した注意点.** 論文と同じ `acceptEdits` と `--allowedTools "Bash(python *)" ...` の設定では、エージェントが Bash のヒアドキュメント（`cat > file <<EOF`）でファイルを書こうとすると権限拒否される。ほとんどの run は Write ツールに切り替えて続行したが、最初の試行では 1 run が「書けたつもり」のまま終わり、`.py` の変更がなかった。論文 Appendix A の「sandbox に拒否されたコマンドがあれば 1 回やり直す」に合わせ、権限拒否があり `.py` が変わらなかった run は無効にして 1 回再実行する扱いにした。本結果の 4 run はすべてこの扱いの後のもので、無効 run はない。

**限界.** 試行数が論文（40 タスク × 2 回）より少ない（2 タスク × 1 回）ため、<mark>割合そのものは比較できず、言えるのは向きが一致したことまで</mark>である。論文の 40 タスクは、このクラウドセッションでは外部コードの実行が権限ポリシーで拒否され、未実行である。ローカルで `python run.py --source paper --reps 2` を実行すれば、論文と同じ 160 run になる。

## 参考資料

- 論文: [arXiv:2610.30571](https://arxiv.org/abs/2610.30571)
- 紹介記事: [AIDB（X）](https://x.com/ai_database/status/2114184481951330365?s=12)
