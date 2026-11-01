# 同じフィードバックをまとめるたびに答えが変わる現象の再現

- 論文: [BGC26] [Same Feedback, Different Answer: Measuring Run-to-Run Instability in Frontier-Model Customer Feedback Analysis](https://arxiv.org/abs/2610.08036)（Viraj Bagal, Raviraja Ganta, Prabhath Chellingi、arXiv:2610.08036）
- 論文の公開日: 2026-10-06（v1）
- 再現日: 2026-11-01

> [!IMPORTANT]
> RESULT_PLACEHOLDER

## 論文の主張

**背景.** 「今月の顧客の不満のトップは何か」という問いに、AI エージェントは毎回もっともらしく答える。だが運用で使う答えは繰り返しに耐えなければならない。同じ記録、同じ質問、同じ設定なら、次の実行でテーマの集合や件数が大きく変わってはならない。テーマはダッシュボードの分類になり、順位はロードマップを左右し、件数は優先順位を決めるからである。モデルの提供元は temperature を 0 にしても出力が完全には固定されないと明記しており、この「出力のずれ」が実際にどれだけ起きるかは分かっていなかった。

**測り方.** 答えは「テーマ名、件数、要約、裏づけとなる記録 ID（5 件まで）」の順序つきリストで、引用は含めない。2 つの実行を比べるには、まず言い換えられたテーマ名を意味的に一対一で対応づける（埋め込みのコサイン類似度 0.82 以上、対応数を最大化してから類似度合計を最大化）。その上で次の距離を全実行ペアで平均する（いずれも小さいほど安定）。

- theme churn（主指標）: 対応づかなかったテーマの割合（Sørensen–Dice の補数）
- volume disagreement: 対応したテーマの件数の相対差
- rank instability: 対応したテーマの順位の Kendall τb から求めた距離
- birth/death: 片方にしか現れないテーマの率
- evidence churn: 裏づけ ID 集合の Jaccard 距離（5 件しか出さないので副次指標）

**比較した 3 つの設計.** (1) raw: モデルに全記録を 1 回で渡して分類させる。(2) taxonomy-free 階層: 記録を 10 の固定バッチに分け、10 の worker が独立に分析し、1 回の統合呼び出しでまとめる（1 答につき 11 回の確率的な呼び出し）。(3) taxonomy-grounded agent（TGA）: 分類体系（テーマ、サブテーマ）と記録単位の予測を先に作って保存し、質問にはそれを参照して答える。

**観察した現象.**
- 8 つのフロンティアモデルを 100 件のコーパスで 10 回ずつ走らせると、<mark>最も安定した raw モデル（Claude Fable 5）でも theme churn は 0.616</mark>、他は 0.657〜0.877。TGA は 135 ペアすべてで churn、順位、birth/death、件数の距離が 0。
- 100、1,000、5,000 件と増やすと raw の churn は 0.552、0.623、0.726 と上がる。TGA は 0.013、0.148、0.033。
- Claude Opus 4.8 と 1,000 件に固定した対照実験では、プロンプトを minimal、bottom-up、consistency-first の 3 種で比べ、<mark>consistency-first が最も安定したが churn は 0.803</mark> で、TGA には遠く及ばない。<mark>raw 0.765、階層 0.841 に対し TGA は 0.104（86〜88% 減）</mark>で、対応したテーマの件数の不一致は 0。階層化（小分け）だけでは安定しない。
- 順位の指標は対応したテーマの間でしか定義できず、raw では 135 ペア中 47 ペアしか定義されない。小さな数値は「残った少数のテーマの順序は保たれた」ことしか意味しない。
- 安定性は正しさではない。同じ誤りを繰り返すこともありうる。また TGA の安定性は分類体系を固定した条件つきで、作り直せば不安定さは取り込み時に移る。

## 実験環境

| 項目 | 論文 | 本再現 |
|---|---|---|
| モデル | 8 モデルの比較、対照実験は Claude Opus 4.8（provider 既定の推論設定）。TGA の supervisor は Claude Sonnet 4.6 / Opus 4.8 | Claude Code 2.1.310 のヘッドレス実行（`claude -p`、ツール無し、`--json-schema` で構造化出力）で claude-sonnet-5-5 と claude-opus-5-5 |
| コーパス | 匿名化された多言語の企業顧客サポートの記録。100 / 1,000 / 5,000 件 | Sonnet 5.5 に書かせた架空の銀行アプリへの意見 300 件（日本語 9 件を含む）。ファイルに固定 |
| 質問 | 3 問（原文を使用） | 同じ |
| 実行回数 | セルあたり 10 回 | 同じ |
| raw / 階層のプロンプト | minimal、bottom-up、consistency-first の 3 種 | 同じ趣旨の 3 種を自作（論文の原文は非公開） |
| 階層 | 10 バッチ × 100 件 + 統合 1 回 | 10 バッチ × 30 件 + 統合 1 回 |
| TGA | 本番のテーマストア（テーマ、サブテーマ、記録単位の予測） | 分類体系を 1 回構築して全記録を分類し JSON に保存。各実行はストアの要約（テーマ、定義、件数、代表 ID）だけを見て答える |
| テーマ名の対応づけ | text-embedding-3-large、cos ≥ 0.82、しきい値 0.76〜0.90 で掃引 | Sonnet 5.5 がテーマ名ペアの類似度を 0〜1 で判定、しきい値 0.70 / 0.85 / 0.95 で掃引 |
| 実行場所 | 著者の環境 | Claude Code のクラウドセッション（Linux コンテナ） |

## 準備したもの

| パス | 内容 |
|---|---|
| `make_corpus.py`, `corpus/feedback-300.json` | 固定コーパスの生成器と生成結果（12 の話題を指定して 25 件ずつ書かせ、シャッフルしてタイムスタンプと ID を付与） |
| `corpus.py` | 定型文からの合成コーパス（最初の試走用。きれいすぎて不安定さが出ないため本実験では不使用） |
| `prompts.py` | 3 つの質問、共通の出力スキーマ、3 種のシステムプロンプト、TGA の構築・分類・回答プロンプト、対応づけ判定のプロンプト |
| `run.py` | raw / 階層 / TGA の実行と記録。`--taxonomy-rebuilds` で分類体系の作り直しも記録 |
| `align.py` | 実行ペアごとのテーマ名の類似度判定（キャッシュ付き） |
| `summarize.py` | 論文の 5 指標をセルごとに集計し、質問間のマクロ平均としきい値の掃引を出す |

## 手順

1. `python make_corpus.py` で 300 件のコーパスを一度だけ生成して固定する。
2. `python run.py --model sonnet --runs 10 --systems "raw:consistency_first,raw:minimal,raw:bottom_up,hierarchy:consistency_first,tga" --taxonomy-rebuilds 5` で、3 質問 × 5 システム × 10 回の答えを `runs/answers-sonnet.jsonl` に記録する。TGA は最初に分類体系の構築と全記録の分類を行い `runs/tga_store-sonnet.json` に保存する。Opus 5.5 は raw（consistency-first）と TGA のみ。
3. `python align.py runs/answers-sonnet.jsonl` で、同じセルの全実行ペアについてテーマ名の類似度を判定し、キャッシュに保存する。
4. `python summarize.py runs/answers-sonnet.jsonl --sweep` で 5 指標とマクロ平均を出す。

## 結果

RESULTS_PLACEHOLDER

## 考察

DISCUSSION_PLACEHOLDER

## 参考資料

- 論文: [arXiv:2610.08036](https://arxiv.org/abs/2610.08036)
- 紹介記事: [AIDB「AIに大量の文章を『まとめて』と頼むたびに結論が変わるのを、ほぼ止める」](https://ai-data-base.com/timeline/read/135209)、[AIDB（X）](https://x.com/ai_database/status/2115692105498566933?s=12)
