# ToDo（ローカルで行う）

## Codex でも同じ質問を試す

クラウドセッションからは OpenAI に届かないので、ローカルにクローンしてから行う。

- [ ] Codex CLI を入れてログインする（`npm install -g @openai/codex`、`codex login`）。
- [ ] `run_codex.py` を数問で試す。Codex CLI 0.167.2 のヘルプでオプションを確かめて書いたが、まだ一度も実行していない。
  ```bash
  python run_codex.py --limit 3 --langs en --out results/codex-test
  ```
  - 質問ごとに空の作業ディレクトリと、`auth.json` だけを写した `CODEX_HOME` で `codex exec` を呼ぶ（AGENTS.md や config.toml を混ぜないため）。
  - 実際に応答したモデル名が `model_used` に入るか確かめる。入らなければ `--json` の出力からモデル名を拾う処理を直す。
- [ ] 使えるモデルを並べて走らせる（`codex exec -m <モデル>`。推論の強さは `-c model_reasoning_effort=low` などで変えられる）。
  ```bash
  python run_codex.py --model <モデル> --langs en,ja,zh,es,ar,sw --out results/codex-<モデル>
  ```
- [ ] 判定と集計は Claude と同じスクリプトで行う。
  ```bash
  python judge.py results/codex-<モデル>
  python summarize.py results/sonnet results/codex-<モデル>
  ```
- [ ] 結果を README（または拡張研究の README）に足す。
