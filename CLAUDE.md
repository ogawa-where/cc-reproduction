# 引き継ぎメモ

論文で報告された Claude Code の現象を再現するリポジトリ。会話は日本語。

- ディレクトリは `YYYYMMDD_<引用キー>/`（著者の頭文字と年。拡張研究は `-ext`）。論文の原文は入れない。
- README は、先頭にリンクと日付、`> [!IMPORTANT]` に再現できたか否か、論文の主張、実験環境、準備したもの、手順、結果、考察（限界を含む）、参考資料（論文と紹介記事だけ）。重要な数値は `<mark>`。本文は `yomiyasu` で推敲する。
- トップの README は `scripts/readme_tables.py` に追記して `python scripts/readme_tables.py --write` で再生成する。
- コミットは ogawa-where の名義で、Claude の署名は入れない。メッセージは日本語で `feat:` などの prefix と `[引用キー]` を付け、細かく分ける。PR も日本語で、署名やフッターは入れない。
