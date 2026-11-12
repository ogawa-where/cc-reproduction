# 場所を伏せた文化の質問に、どの国を選んで答えるかの再現

- 論文: [FPC26] [Why are all LLMs Obsessed with Japanese Culture? On the Hidden Cultural and Regional Biases of LLMs](https://arxiv.org/abs/2604.21751)（Joseba Fernandez de Landa、Carla Perez-Almendros、Jose Camacho-Collados、arXiv:2604.21751、Findings of EMNLP 2026）
- 論文の公開日: 2026-04-23（arXiv v1）
- 再現日: 2026-11-12

> [!IMPORTANT]
> **一部再現できた。** 英語の質問では、Claude Code（Sonnet 5.5、Haiku 5.5）が own（英語圏）以外で最も多く参照した国は<mark>日本</mark>だった（Sonnet 67 回で 2 位の中国 42 回を上回り、Haiku も 32 回対 24 回）。主に選んだ国でも日本が首位で、論文の「日本への偏り」は英語では再現した。一方、中国語・スペイン語・アラビア語では<mark>米国が首位で日本は 2〜3 位</mark>にとどまった。論文（8 モデルの合計）ではこの 3 言語でも日本が米国を上回っており、結果が異なる。6 言語をまとめると米国（Sonnet 276 回）が日本（215 回）を上回る。入力言語の国（own）に参照が集中すること、低資源のスワヒリ語で own の割合が最も高いことは、論文と一致した。

## 論文の主張

**背景.** LLM の文化的な偏りはこれまで欧米、とくに米国寄りだと報告されてきた。ただし多くの評価はあらかじめ決めた正解や人の回答と比べる形式で、場所を指定しない自由な質問にモデルがどの国を思い浮かべるかは調べられていなかった。

**測り方.** 文化を 11 領域 66 小分類に分け、小分類ごとに 20 問、計 1,320 問の「場所を伏せた質問」（CROQ）を作った。例は "What traditional dances exist?" や "What foods are for daily meal?" である。これを 24 言語に翻訳し、計 31,680 問とした。各質問に "Be brief. Choose yourself the place." を付けてモデルに答えさせ、判定モデル（gpt-4o-mini）が答えに出てくる国を最大 5 つ取り出す。国が無ければ無回答（NA）とする。判定プロンプトは 3 種の候補から手作業の評価（264 件）で選んだもので、正解率は 98% だった。指標は次のとおり。

- own: 入力言語を公用語とする国への参照の割合
- 国別の参照数（own を除く）
- diversity: 参照された異なる国の数
- entropy: 参照の分布の正規化エントロピー（大きいほど偏りが小さい）

**観察した現象.**
- 8 つのフロンティアモデル（gpt-4o-mini、gemini-2.5-flash、claude-3.5-haiku ほか）では、参照の <mark>43〜78% が入力言語の国（own）</mark>に向かう。Claude 3.5 Haiku は 65%。
- own を除くと、<mark>8 モデル中 6 モデルで日本が最も多く参照される</mark>（本文の別の箇所では「5 モデルが日本、2 モデルが米国」）。次が米国、インド、中国、フランス。Claude 3.5 Haiku も日本 1,601 回、米国 1,200 回で日本が首位。言語別でも中国語、スペイン語、アラビア語などで日本が米国を上回る（Table 9、8 モデルの合計）。
- 日本と米国はすべての領域で上位にいる。ただし地理と経済では米国が日本を上回り、政治と歴史では日本は 3〜4 位に下がる。
- 低資源言語（スンダ語、アッサム語、アムハラ語、ハウサ語、バスク語など）ほど own と NA が多く、diversity が小さい。diversity と CommonCrawl の言語別の量の順位相関は 0.843。
- ベースモデルでは参照が広く分散し、SFT の後に米国と日本への集中が強まる（OLMo の比較）。偏りは事前学習ではなく事後学習で生じる、と論文は結論づける。

## 実験環境

| 項目 | 論文 | 本再現 |
|---|---|---|
| 回答するモデル | 8 つのフロンティアモデル（Claude は claude-3.5-haiku）、OpenRouter の既定設定 | Claude Code 2.1.322 のヘッドレス実行（`claude -p --tools ""`、Claude Code の既定のシステムプロンプト）で claude-sonnet-5-5 と claude-haiku-5-5 |
| 質問 | CROQ。66 小分類 × 20 問 = 1,320 問を GPT-5.1 で作り、手で確認 | 論文の分類（Table 5）に沿って Opus 5.5 に作らせ、国名・地域名を含むものを機械的に除いた 66 小分類 × 5 問 = 330 問 |
| 言語 | 24 言語（自動翻訳と後編集） | 6 言語（en、ja、zh、es、ar、sw）。翻訳は Sonnet 5.5 |
| 付ける指示 | "Be brief. Choose yourself the place."（言語ごとに翻訳） | 同じ |
| 判定 | gpt-4o-mini、Middle プロンプト（Figure 7）、1 回答ずつ | claude-haiku-5-5。Middle プロンプトをシステムプロンプトにそのまま使い、15 回答ずつまとめて JSON で返させる。まとめるための指示で、国は主権国家の英語名で返し、地域や都市はその国に直すよう加えた。主に選んだ国（primary）も合わせて返させる |
| own の定義 | 入力言語を公用語とする国 | 同じ（`summarize.py` に一覧） |
| 学習段階の比較 | ベース、SFT、指示調整済みの OLMo など | 対象外（Claude のベースモデルは使えない） |
| 実行場所 | 著者の環境 | Claude Code のクラウドセッション（Linux コンテナ）。各呼び出しは空の作業ディレクトリと専用の設定ディレクトリで行う |

## 準備したもの

| パス | 内容 |
|---|---|
| `taxonomy.py` | 論文の 11 領域 66 小分類（Table 5）と、領域ごとの例題 |
| `make_questions.py` | 英語の質問の生成（小分類ごとに 10 問作らせ、地名フィルタを通った先頭 5 問を採用）と翻訳 |
| `questions/` | 6 言語の質問（各 330 問）と、英語の候補（`en_candidates.json`） |
| `cc.py` | CLAUDE.md、記憶、MCP、ユーザー設定が混ざらない `claude -p` 呼び出し |
| `run.py` | 1 問につき 1 回の呼び出しで回答を集める（再開可能） |
| `judge.py` | 論文の判定プロンプトで、回答ごとに国（最大 5）と主に選んだ国を取り出し、ISO コードにそろえる |
| `summarize.py` | own、NA、own を除いた国別の参照数、diversity、entropy を言語ごとに集計する |
| `run_codex.py`, `TODO.md` | Codex で同じ質問を試すためのスクリプトと手順（ローカルで行う。未実行） |
| `results/` | 回答（`answers-<言語>.jsonl`）、判定（`judged-<言語>.jsonl`）、ログ |

## 手順

1. 質問を作る。

   ```bash
   python make_questions.py en
   python make_questions.py translate ja zh es ar sw
   ```

2. モデルごとに回答を集めて判定する。

   ```bash
   python run.py --model sonnet --langs en,ja,zh,es,ar,sw --workers 8 --out results/sonnet
   python judge.py results/sonnet
   python run.py --model haiku  --langs en,ja,zh,es,ar,sw --workers 8 --out results/haiku
   python judge.py results/haiku
   ```

3. 集計する。

   ```bash
   python summarize.py results/sonnet results/haiku
   python summarize.py results/sonnet --langs en --by-domain
   ```

## 結果

各モデル 6 言語 × 330 問 = 1,980 回答、エラーは 0。判定は 15 回答ずつまとめて 132 回行った。抜き取った 24 件（各言語 4 件、`results/judge_check.md`）を手で確かめたところ誤りは無かった。参照数は 1 回答あたり最大 5 か国で数える。

### 言語別の集計

| モデル | 言語 | own の割合 | NA | diversity | entropy | own を除く上位の国（参照数） | 日本の順位 |
|---|---|---|---|---|---|---|---|
| Sonnet 5.5 | en | 0.43 | 35 | 86 | 0.77 | <mark>JP 67</mark>、CN 42、FR 27、DE 26 | <mark>1</mark> |
| Sonnet 5.5 | ja | 0.45 | 17 | 67 | 0.61 | US 52、CN 27、IN 26、GB 25 | （own） |
| Sonnet 5.5 | zh | 0.34 | 21 | 86 | 0.66 | US 85、JP 52、IN 36、GB 34 | 2 |
| Sonnet 5.5 | es | 0.50 | 35 | 81 | 0.73 | US 55、JP 43、CN 30、IN 26 | 2 |
| Sonnet 5.5 | ar | 0.41 | 78 | 88 | 0.81 | US 51、JP 41、IN 30、GB 28 | 2 |
| Sonnet 5.5 | sw | <mark>0.61</mark> | 32 | 71 | 0.62 | US 33、GB 22、DE 16、ZA 14 | 7 |
| Haiku 5.5 | en | 0.49 | 69 | 67 | 0.74 | <mark>JP 32</mark>、CN 24、FR 18、DE 15 | <mark>1</mark> |
| Haiku 5.5 | ja | 0.49 | 65 | 62 | 0.59 | US 36、CN 20、FR 17、GB 14 | （own） |
| Haiku 5.5 | zh | 0.38 | 76 | 81 | 0.67 | US 51、JP 28、IN 22、FR 21 | 2 |
| Haiku 5.5 | es | 0.54 | 46 | 58 | 0.71 | US 40、FR 22、JP 21、IT 14 | 3 |
| Haiku 5.5 | ar | 0.41 | 108 | 67 | 0.83 | US 45、JP 25、GB 23、CN 22 | 2 |
| Haiku 5.5 | sw | <mark>0.57</mark> | 62 | 56 | 0.62 | US 29、GB 18、FR 16、DE 14 | 5 |

- 主に選んだ国（primary）で見ても、英語では日本が首位（Sonnet 41 回、2 位の中国 12 回。Haiku 22 回、中国 11 回）。英語以外では、Sonnet のスペイン語（JP 19 回、US 15 回）を除いて米国が首位。
- 6 言語の合計（own を除く）は、Sonnet が US 276、JP 215、CN 134、IN 131、GB 129。Haiku が US 201、JP 118、FR 115、GB 86、CN 83。

### 論文との比較（own を除いた首位の国）

| 言語 | 論文（8 モデルの合計、Table 9） | Sonnet 5.5 | Haiku 5.5 |
|---|---|---|---|
| en | JP 2,893 | JP 67 | JP 32 |
| ja | US 736 | US 52 | US 36 |
| zh | <mark>JP 2,064</mark>（US 1,460） | <mark>US 85</mark>（JP 52） | US 51（JP 28） |
| es | <mark>JP 843</mark>（US 588） | <mark>US 55</mark>（JP 43） | US 40（JP 21） |
| ar | <mark>JP 504</mark>（US 396） | <mark>US 51</mark>（JP 41） | US 45（JP 25） |
| sw | US 389（JP 230） | US 33（JP 12） | US 29（JP 12） |

- own の割合は論文の Claude 3.5 Haiku（24 言語で 0.65）より低い 0.34〜0.61。論文の言語別（Table 9、8 モデルの合計）は en 0.31、ja 0.59、zh 0.48、es 0.66、ar 0.69、sw 0.78 で、スワヒリ語が最も高い点は同じ。
- 英語の領域別では、日本は芸術・信仰・社会・食・メディア・教育で首位、政治と歴史では順位を下げ（歴史はフランスが首位）、経済と地理では中国が首位だった（Sonnet）。日本が政治と歴史で順位を落とす点は論文と同じ。

## 考察

- **英語では日本への偏りが再現した.** 場所を選ばせると、英語の質問では英語圏の国を除いて日本が最も多く選ばれ、人口や経済規模で日本を上回る中国より多い。日本が選ばれやすいのは芸術や信仰、社会の習慣などの質問で、政治と歴史では順位を下げる。後者は論文と同じ傾向である。
- **他の言語では米国が上回る.** 論文では中国語・スペイン語・アラビア語でも日本が米国を上回ったが、Claude 5.5 系では 3 言語とも米国が首位で、日本は 2 位前後だった。論文の言語別の国別参照数は 8 モデルの合計で、Claude 3.5 Haiku 単独の値は示されていない。そのため、Claude が以前から米国寄りだったのか、新しいモデルで変わったのかは区別できない。
- **own への集中と低資源言語の傾向は再現した.** どの言語でも own への参照が最も多く、スワヒリ語は own の割合が最も高く、diversity も低い側（Sonnet 71、Haiku 56）だった。ただし Haiku はスペイン語でも diversity が 58 と低く、diversity は資源量だけでは決まらない。
- **Claude Code の既定の文脈で測っている.** 回答は Claude Code のシステムプロンプトの下で得た。リポジトリ内で呼ぶと CLAUDE.md の「会話は日本語」が効き、英語の質問にも日本語で日本の例を答える（試走で確認）。エージェントの設定ファイルが文化的な選択を大きく動かしうるので、測定では隔離が欠かせない。

### 限界

- 質問は論文の CROQ ではなく、論文の分類に沿って Opus 5.5 に作らせた 330 問で、手による確認はしていない。言語も 6 つだけで、論文の 24 言語より少ない。
- 判定は gpt-4o-mini ではなく Haiku 5.5 で、15 回答ずつまとめて判定した。手で確かめたのは 24 件だけ。
- モデルは Sonnet 5.5 と Haiku 5.5 だけで、論文の Claude 3.5 Haiku は呼べなかった。どのモデルが特に日本寄りかは拡張研究で調べる。
- 学習段階（ベースモデルと SFT）の主張は検証していない。
- 各質問は 1 回ずつで、同じ質問を繰り返したときのばらつきは測っていない。

## 参考資料

- 論文: [arXiv:2604.21751](https://arxiv.org/abs/2604.21751)、[ACL Anthology（Findings of EMNLP 2026）](https://aclanthology.org/2026.findings-emnlp.1307/)
- 紹介記事: [AIDB（X）](https://x.com/ai_database/status/2048006029628350724?s=12)、[AIDB](https://ai-data-base.com/timeline/read/107575)
