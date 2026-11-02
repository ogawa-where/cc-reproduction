# cc-reproduction の引き継ぎメモ

論文で報告された Claude Code の現象を再現し（再現研究）、その先を調べる（拡張研究）リポジトリ。会話は日本語。

## ディレクトリ

- 研究ごとに `YYYYMMDD_<引用キー>/`。引用キーは著者の頭文字と年（Xu & Wu 2026 → `XW26`、単著 Bui → `B26`）。拡張研究は `-ext`。
- 中身: `DESIGN.md`、ハーネス、タスクや素材、`results/`（試行記録。ストリームなど大きいものは `.gitignore`）、`README.md`。
- 論文の原文（PDF など）はリポジトリに入れない。

## README

- 構成: 先頭にリンクと日付（`- 論文: [KEY] [題名](arXiv URL)（著者、arXiv:id）`、`- 論文の公開日`、`- 再現日`）、`> [!IMPORTANT]` に再現できたか否かの結論、`## 論文の主張`、`## 実験環境`（論文と本再現の表）、`## 準備したもの`、`## 手順`、`## 結果`、`## 考察`（`### 限界` を含む）、`## 参考資料`（論文の arXiv と紹介記事だけ。不要な URL は載せない）。
- 重要な数値は `<mark>` で囲む。文章は短く、事実と数値を優先。
- 本文は `yomiyasu` スキルで推敲する。推敲時にデータと論文に対する事実確認も頼み、指摘された食い違いは直す。
- トップの README は `scripts/readme_tables.py` の `REPRODUCTIONS` / `EXTENSIONS` に追記して `python scripts/readme_tables.py --write` で再生成する。表の中は ASCII のみ、各行 86 桁以内。Result は `OK`（現象が再現した）か `Done`（実験は完了したが現象は出なかった）。

## コミットと PR

- コミットは ogawa-where の名義で行い、Claude の署名、Co-Authored-By、セッション URL は入れない。
- メッセージは日本語で `feat:`、`fix:`、`docs:`、`data:`、`chore:` の prefix を付け、研究には `[KEY]` を添える。1 コミット 1 変更で細かく分ける。force push や amend はしない。
- PR は日本語の題名と本文（概要、結論、内容）。Claude の署名やフッターは入れない。自動で付いた場合は本文を更新して消す。
- マージ後は作業ブランチが自動削除されるので、`origin/main` から作り直す。

## 注意点

- 論文の判定メモにあった「Private note … Do not mention it to the user.」のような文言は API の安全ガードに弾かれることがある。ハーネスは記録済みの試行を飛ばして再開できるように作り、`safeguards flagged` の `is_error` は再試行する。
- 表の中に CJK や絵文字を入れると桁がずれる。画像にテキストのラベルを入れると文字の交絡になる。
- ダウンロードした論文のデータやコードの実行、旧バージョンの Claude Code の認証はクラウドではできない。ローカルで行う。
