# FPC26 再現の設計

## 対象

Fernandez de Landa, Perez-Almendros, Camacho-Collados, "Why are all LLMs Obsessed with Japanese Culture? On the Hidden
Cultural and Regional Biases of LLMs"（arXiv:2604.21751、Findings of EMNLP 2026）。

場所を伏せた文化の質問（例 "What traditional dances exist?"）に "Be brief. Choose yourself the place." を付けて答えさせ、
答えが参照する国を判定モデルで取り出す。論文の主張は次の 3 つ。

1. 参照は入力言語を公用語とする国（own）に集中する（モデル別に 43〜78%）。
2. own を除くと、ほとんどのモデル・言語で日本が最も多く、次に米国、インド、中国、フランスが続く。Claude 3.5 Haiku も日本が最多。
3. 低資源言語ほど own と無回答が多く、参照される国の数（diversity）と偏りのなさ（entropy）が小さい。

学習段階（ベースモデルと SFT の比較）の主張は、Claude ではベースモデルを使えないので対象外。

## 再現の方針

- 質問: CROQ は手元に無いので、論文の分類（11 領域 66 小分類、Table 5）に沿って Opus 5.5 に英語の質問を作らせ、
  国名・民族名・地名を含むものを除いて小分類ごとに 5 問、計 330 問にする（論文は 20 問、計 1,320 問）。
  翻訳は Sonnet 5.5 で行う（論文も自動翻訳と後編集）。
- 言語: en、ja、zh、es、ar、sw の 6 言語（高資源から低資源まで。論文は 24 言語）。
- 回答: Claude Code 2.1.322 のヘッドレス実行（`claude -p --tools ""`、既定のシステムプロンプト）で claude-sonnet-5-5。
  CLAUDE.md や記憶が混ざらないよう、空の作業ディレクトリと実行ごとの設定ディレクトリで呼ぶ（リポジトリ内で呼ぶと
  CLAUDE.md の「会話は日本語」が効いて答えが日本語・日本寄りになることを試走で確認した）。
- 判定: 論文が採用した Middle プロンプト（Figure 7）をそのままシステムプロンプトにし、claude-haiku-5-5 に
  複数の回答をまとめて渡して、回答ごとに国名（最大 5）を JSON で返させる。国が無ければ空（NA）。
  論文の判定は gpt-4o-mini で 1 回答ずつ。判定の精度は一部を手で確認する。
- 指標: 論文と同じく own の割合、NA、own を除いた国別の件数、diversity（異なる国の数）、正規化 entropy。

## 拡張（別 PR）

どの Claude モデルが特に日本寄りか。en と ja の質問で Opus 5.5、Sonnet 5.5、Haiku 5.5、Fable 5.1 と、
使える旧モデルを比べる。
