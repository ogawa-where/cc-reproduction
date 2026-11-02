# cc-reproduction の進め方

このリポジトリは、論文で報告された Claude Code の現象を再現し（再現研究）、その先を調べる（拡張研究）ためのものです。会話は日本語で行います。

## 役割分担（モデル）

- 最上位の判断（設計、結果の解釈、README の最終確認）はメインのセッションが行う。
- ハーネスやタスクの作成、README の下書き、推敲などの作業は Opus 5.5 のサブエージェントに委任する。ごく軽い作業は Sonnet 5.5。
- 実験の対象モデルは原則 Opus 5.5 と Sonnet 5.5。論文の主張に必要なら上位モデルも使う。

## ディレクトリ

- 研究ごとに `YYYYMMDD_<引用キー>/` を切る。引用キーは著者の頭文字と年（Xu & Wu 2026 → `XW26`、単著 Bui → `B26`、5 人以上でもそのまま並べる）。拡張研究は `-ext` を付ける。
- 各ディレクトリに置くもの: `DESIGN.md`（設計メモ）、ハーネス（`run.py`、`summarize.py` など）、タスクや素材、`results/`（試行記録・差分・ログ。ストリームや作業ツリーは `.gitignore` で除外）、`README.md`（報告）。
- 論文の PDF は添付してもらい `pdftotext -layout` で読む（arxiv.org、x.com、ai-data-base.com はクラウドからは届かない）。論文の原文はリポジトリに入れない。

## 進める順序

1. 論文を読み、主張・手法・指標・主要な数値を抜き出す。引用キーが正しいか確認する。
2. `DESIGN.md` に再現の設計を書く（何を Claude Code でどう測るか、論文との差）。
3. ハーネスとタスクを作り、1 タスクで試走してから本番を走らせる（本番はバックグラウンドで、ログをファイルに残す）。
4. 結果を集計し、`README.md` を書く。結果が出る前に静的な節を先に書いてよい。
5. README の本文を `yomiyasu` スキルで推敲する（Opus のサブエージェントに任せ、データと論文に対する事実確認も同時に頼む）。指摘された事実の食い違いは必ず直す。
6. トップの README に追加する。`scripts/readme_tables.py` の `REPRODUCTIONS`（または `EXTENSIONS`）に追記して `python scripts/readme_tables.py --write` を実行する。表の中は ASCII のみ、各行 86 桁以内。
7. 変更ごとに細かくコミットし、push して PR を作る。

## ハーネスの約束事

- Claude Code はヘッドレス（`claude -p`）で使う。`--input-format stream-json --output-format stream-json --verbose`、必要に応じて `--tools ""`、`--json-schema`、`--system-prompt`、`--append-system-prompt`、`--allowedTools`、`--permission-mode acceptEdits`。
- 実行ごとに `CLAUDE_CONFIG_DIR` を分け、環境変数の `CLAUDE*`、`ANTHROPIC*` を落とし、`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` と `DISABLE_AUTOUPDATER=1` を付ける。
- 多ターンの分岐は `--session-id <uuid>` で Turn 1 を走らせ、`--resume <id> --fork-session` で Turn 2 を分ける。
- 記録済みの試行を飛ばして再開できるように作る。API の安全ガード（`safeguards flagged`）で `is_error` になることがあるので、同じ条件から再試行する。
- 試行の記録は JSONL（1 行 1 試行）。集計は Wilson 区間付きで出す。

## README の構成

先頭にリンクと日付、`> [!IMPORTANT]` の結論、続いて `## 論文の主張`、`## 実験環境`（論文と本再現の表）、`## 準備したもの`、`## 手順`、`## 結果`、`## 考察`（`### 限界` を含む）、`## 参考資料`（論文の arXiv と紹介記事の X 投稿だけ。不要な URL は載せない）。

- 冒頭は `- 論文: [KEY] [題名](arXiv URL)（著者、arXiv:id）`、`- 論文の公開日`、`- 再現日`。
- 重要な数値は `<mark>` で囲む。論文の数値はすべて原文で確認する。
- 文章は短く、事実と数値を優先する。再現できたか否かを必ず書く。トップ README の Result は `OK`（現象が再現した）か `Done`（実験は完了したが現象は出なかった）。

## コミットと PR

- コミットは ogawa-where の名義で行い、Claude の署名、Co-Authored-By、セッション URL は入れない。
- メッセージは日本語で、`feat:`、`fix:`、`docs:`、`data:`、`chore:` の prefix を付け、研究には `[KEY]` を添える（例 `feat: [B26] 2ターン実験ハーネスを追加`）。1 コミット 1 変更。
- 履歴の書き換え（force push、amend）はしない。コミットは最初から分けて作る。
- PR は日本語の題名（`feat: [KEY] …`）と本文（概要、結論、内容）。Claude の署名やフッターは入れない。GitHub MCP が自動でフッターを付けた場合は本文を更新して消し、消えたことを確認する。
- マージ後は作業ブランチが自動削除されるので、`git fetch origin main && git checkout -B <作業ブランチ> origin/main` で作り直してから次の作業を始める。

## 注意点

- 表の中に CJK や絵文字を入れると桁がずれる。
- 画像にテキストのラベルを入れると文字の交絡になる。
- ダウンロードした論文のデータやコードはクラウドでは実行を拒否されることがある。ローカルで実行する手順として残す。
- 旧バージョンの Claude Code の A/B は、クラウドでは認証できないためローカルで行う。
