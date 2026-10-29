# 圧縮要約が「どう作業するか」の制約を落とす現象の再現

- 論文: [SBBAA26] [Benchmarks Are Surprisingly Compaction-Friendly](https://arxiv.org/abs/2610.31778)（Jeanne Salle, Hardik Bhatnagar, Matthias Bethge, Sahar Abdelnabi, Maksym Andriushchenko、arXiv:2610.31778、公開データ [aisa-group/compaction](https://github.com/aisa-group/compaction)）
- 論文の公開日: 2026-10-22（v1）
- 再現日: 2026-10-29

> [!IMPORTANT]
> RESULT_PLACEHOLDER

## 論文の主張

**背景.** 長いタスクではエージェントの文脈が上限に達するため、足場（Claude Code、Codex CLI、OpenCode など）はそれまでの履歴をモデル自身に要約させ、要約だけを残して続行する。これを圧縮（compaction）と呼ぶ。要約は情報を捨てる設計なので、タスクの制約や指示、以前の判断の理由が黙って失われうる。

**観察した現象.** 著者らは OpenCode を足場に固定し、5 つの圧縮方式を実装して、4 つのフロンティアモデル（Claude Opus 4.6、GPT-5.3-Codex、GPT-5.4、Gemini 3.1 Pro Preview）を 3 つの長時間ベンチマーク（PaperBench、ProgramBench、PostTrainBench）で評価した。

- Q1/Q2（性能）: 1M 文脈のモデルでは圧縮のしきい値（160K〜380K トークン）は性能に影響しない。既定の自己要約を上回る方式はなく、推論ブロックの削除や小さいモデルによる要約は、モデルによって最大 20 点下げる。
- Q3（制約の侵食）: ProgramBench のタスク文には不正防止ルールが 3 つある（参照実装を複製しない、インターネットを使わない、独自実装にする）。<mark>最初の圧縮要約の時点で平均 0.92 カテゴリが落ち、10 回目で 1.93、30 回目で 2.65</mark> と単調に増える。要約プロンプトが「持続すべき制約」を明示的に求めていても落ちる。モデル差が大きく、1 回の圧縮あたり GPT-5.3-Codex は 2.73、GPT-5.4 は 1.76、Claude Opus 4.6 は 0.51 カテゴリを落とす。
- Q4（実セッション）: 実ユーザーと Claude Code のセッション集 SWE-chat から圧縮を含む 44 セッションを取り、圧縮前にユーザーが与えた制約 269 個を LLM で抽出、次の圧縮要約に残っているかを別の LLM 判定器で判定した。<mark>全体では 81% が保持され 19% が欠落したが、カテゴリで大きく違う</mark>。何を作るか（feature requirement、96 個）は 6.2% しか落ちないのに、どう作業するか（process instruction、39 個）は 35.9%、何に触れないか（scope exclusion、38 個）は 36.8% 落ちる。<mark>約 6 倍の差</mark>である。

**原因の説明.** ベンチマークは目的が固定で、エージェントの進捗はファイルとして残るため、要約が捨てたものの大半はファイルを読み直せば回復できる。だから圧縮しても得点は下がらない（compaction-friendly）。回復できないのは、文脈にしか存在しない制約である。要約を書くモデルは「続行に必要なこと」を優先し、制約は続行には不要（正しく続行するためにだけ必要）なので落とされやすい。

**提言.** 圧縮の評価には、ファイルから回復できない制約を持つタスク（時間とともに指示が変わる多ターンのセッション）が必要である。

## 実験環境

| 項目 | 論文 Q4（SWE-chat） | 本再現 |
|---|---|---|
| 足場 | Claude Code（版はデータ集に依存、2026 年 4 月以前） | Claude Code 2.1.310 |
| 要約を書くモデル | セッションごとに異なる | claude-sonnet-5-5（被験体と同じ） |
| 制約の判定 | Claude Sonnet 5（要約と制約一覧だけを見る盲検判定） | claude-sonnet-5-5、論文 Appendix 6.4.5 のプロンプト |
| カテゴリ分類 | Claude Sonnet 5、論文 Appendix 6.4.6 の 8 分類 | 植え込み時に付与。論文の分類器でも照合 |
| セッション | 実ユーザーの 44 セッション、制約 269 個 | 台本つきセッション 6 本（3 シナリオ × 2 回）、制約 60 個 × 圧縮 3 回 |
| 圧縮の契機 | 自動（文脈上限） | `/compact`（圧縮前 約 12 万トークン）、以後は要約の要約を 2 回 |
| 実行場所 | 著者の環境 | Claude Code のクラウドセッション（Linux コンテナ） |

## 準備したもの

| パス | 内容 |
|---|---|
| `scenarios/A_notes`, `B_pipeline`, `C_site` | 小さな Python リポジトリ（メモ CLI、CSV 集計、静的サイト生成）と台本 `scenario.json`。各 5 ターンで機能追加を頼みながら 7 カテゴリの制約を 19〜21 個植え込む。4〜5 ターン目は約 100KB のログを貼り付けて原因調査を頼み、実セッションのように文脈を膨らませる |
| `fixtures.py` | 貼り付けるログを決定的に生成する（各ログに見つけるべき異常が 1 つ） |
| `prompts/preservation.md`, `prompts/classification.md` | 論文 Appendix 6.4.5（保持判定）と 6.4.6（カテゴリ分類）の判定プロンプト |
| `run.py` | セッションの実行、圧縮、要約の抽出、判定、圧縮後の挙動確認 |
| `summarize.py` | カテゴリ別・圧縮回数別の欠落率（Wilson 95% 区間）と論文値の対比 |

## 手順

1. シナリオの `repo/` を一時ディレクトリにコピーし、空のユーザーレベル CLAUDE.md を持つ専用 `CLAUDE_CONFIG_DIR` で、`claude -p --input-format stream-json --output-format stream-json --permission-mode acceptEdits`（Bash は `python*`/`pytest*` のみ許可）を起動する。
2. 台本の 5 ターンを順に送り、各ターンの終了（`result` イベント）を待つ。
3. `/compact` を送り、`compact_boundary` イベントと、続くユーザーイベントに載る圧縮要約を取り出す（transcript の `isCompactSummary` でも確認）。
4. 要約本文（ハーネスの定型文を除いた部分）と制約一覧だけを判定器に渡し、各制約を preserved / dropped / contradicted に分類する。
5. 圧縮後にプローブのターン（新機能の追加）を送り、触ってはいけないファイルの変更、既存テストの削除、テスト実行の有無、`git commit` の有無を機械的に確認する。
6. ログ貼り付けのターンをもう 1 つ送って `/compact` し、2 回目・3 回目の要約も同じ制約で判定する（論文 Q3 の「要約の要約」）。

```bash
python -m pip install pytest
python run.py --reps 2 --compactions 3 --classify     # 3 シナリオ × 2 回、圧縮 3 回
python summarize.py runs/runs.jsonl --runs
```

## 結果

RESULTS_PLACEHOLDER

## 考察

DISCUSSION_PLACEHOLDER
