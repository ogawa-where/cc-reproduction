# FPC26-ext 設計メモ

## 問い

FPC26 の再現では、英語の質問で Sonnet 5.5 と Haiku 5.5 のどちらも日本を最も多く選んだ。どの Claude モデルが特に日本寄りか。
世代（4 系と 5 系）や大きさ（Haiku、Sonnet、Opus、Fable）で違いがあるか。

## 方法

- 質問と手順は FPC26 と同じ（`../20261112_FPC26/` の `questions/en.json` 330 問、`run.py`、`judge.py`）。英語だけを使う。
  英語では日本が own（英語圏）に入らないので、日本への偏りをそのまま測れる。
- モデル: Fable 5.1、Opus 5.5、Sonnet 5.5、Haiku 5.5、Sonnet 5、Opus 4.7、Opus 4.6、Opus 4.5、Sonnet 4.6、Sonnet 4.5、Haiku 4.5。
  Sonnet 5.5 と Haiku 5.5 は FPC26 の結果を使う。応答したモデル名は `model_used` で確かめる（`claude-opus-4-1` を指定すると
  黙って Opus 5.5 になることを確認したため、使えないモデルは外した）。
- 指標（`compare.py`）:
  - 日本を主に選んだ回答の割合（330 問中。Wilson 95% 区間）
  - own を除いた参照のうち日本の割合
  - own を除いた参照の 2 位の国と、日本との比
  - NA、diversity、entropy（FPC26 と同じ）
