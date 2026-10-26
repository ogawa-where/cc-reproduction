# 古い CLAUDE.md がコードより優先される現象の再現

対象論文: Xu & Wu (2026), *Stale Instruction Files Override the Code in Coding Agents: A One-Sentence Fix*,
arXiv:2610.30571 (https://arxiv.org/abs/2610.30571)。公開データ: https://github.com/WenJing95/stale-docs-data

## 論文が報告している現象

- プロジェクトの指示ファイル（CLAUDE.md / AGENTS.md）には「print() を使え」などの規約が書いてあるのに、
  既存コードは全モジュールが logging を使っている。この**指示ファイルだけが古い**状態を 40 個の
  Python プロジェクトで作り、機能追加を依頼する。
- 指示文なし: 選択の 90.1% が古いファイル側に従った。Claude Code は 80 回中 79 回、最終返答で
  「CLAUDE.md と既存コードが食い違っている」と指摘した上で、**それでもファイル側に従った**。
  Codex CLI は 80 回中 20 回、既存コードをファイルに合わせて書き換え、そのうち 17 回で元のテストが通らなくなった。
- ユーザーレベルの指示ファイル（`~/.claude/CLAUDE.md`）に次の一文を足すと、コード側に従う割合が
  4.2% → 91.4% になり、書き換えはなくなり、テスト通過率は 89.4% → 100% になった。

> When a repository's documentation and its existing code disagree, follow the conventions used
> in the existing code, and in your final reply point out each inconsistency you found between
> the documentation and the code.

- 著者の説明: 指示ファイルはモデルに「指示」として渡り、コードは「ツール出力」として渡る。モデルは
  instruction hierarchy により指示をツール出力より優先するよう訓練されているため、古い記述でも指示として
  扱われる分、コードより優先されてしまう。一文を足すと「コードに従う」こと自体が指示になるので、指示同士の比較になる。

## このディレクトリの構成

| パス | 内容 |
|---|---|
| `run.py` | 再現ランナー。論文 Appendix A と同じフラグで `claude -p` を走らせ、判定・採点・記録まで行う |
| `summarize.py` | `runs.jsonl` を論文の Fig. 5 / Fig. 6 と同じ形に集計する |
| `conditions/A_empty.md`, `conditions/B_fix.md` | 条件 A（空）/ 条件 B（一文）のユーザーレベル CLAUDE.md |
| `criteria/conflict_criteria.md` | 最終返答が「ドキュメントとコードの食い違い」を指摘したかを判定する基準 |
| `mini/tasks/M01`, `M02` | 自作の小さなタスク 2 件（論文と同じ形式。依存なしの動作確認用） |
| `fetch_paper_data.sh` | 論文の公開データ（40 タスク、選択判定器 `judge.py`）を `paper-data/` に取得（gitignore 済み） |

論文の公開データはライセンス表記がないためリポジトリには同梱せず、実行時に取得する。
自作タスクの判定にも論文の `judge.py`（正規表現による選択判定）をそのまま使うので、`mini` でも
`fetch_paper_data.sh` が必要になる。

### 自作タスクの設計（論文と同じ "ファイルは一方、コードは他方" の対立）

| タスク | 既存コードの規約 | 古い CLAUDE.md が要求する規約 | 機能追加 |
|---|---|---|---|
| M01 `notify` | `logging` / `@dataclass` / f-string | `print()` to stderr / `namedtuple` / `str.format()` | `python -m notify.digest INPUT OUTPUT` |
| M02 `fileindex` | `os.path` / `X \| None` / `unittest.TestCase` | `pathlib` / `typing.Optional` / pytest 関数 | `python -m fileindex.report ROOT OUTPUT` |

## 1 回の実行で起きること（`run.py`）

1. タスクの `repo/` を一時ディレクトリ（リポジトリ外。祖先に CLAUDE.md が無い場所）へコピーし、
   `instructions.md` を `CLAUDE.md` として置き、git で baseline コミットを作る。
2. 条件ごとの専用 `CLAUDE_CONFIG_DIR` を作り、その中の `CLAUDE.md` に条件 A/B の内容を置く。
3. 親セッションの `CLAUDE*` / `ANTHROPIC*` などの環境変数を除いた上で（Appendix A）、
   `claude -p --model sonnet --permission-mode acceptEdits --output-format stream-json --verbose
   --strict-mcp-config --allowedTools "Bash(python *)" ... --disallowedTools "Bash(pip *)" ...`
   を実行し、機能要求を標準入力で渡す（制限時間 1800 秒）。
4. `git diff --no-renames --unified=100000` を取り、論文の `judge.py` で各選択を
   `follow_file` / `follow_code` / `neither` に分類する。既存の `.py` から 20 行以上を削除していれば「書き換え」とする。
5. 元のテストファイルを戻し、held-out の機能テストと一緒に pytest を 1 回実行する。
6. 最終返答だけを別モデル（Opus、ツール無し、`--safe-mode`）に見せ、食い違いを指摘したかを YES/NO で判定する。
7. `runs/runs.jsonl` に 1 行追記し、`runs/<run id>/` に `stream.jsonl`、`diff.patch`、`final_reply.md`、`record.json` を保存する。

## 使い方

```bash
cd stale-instruction-override
./fetch_paper_data.sh                      # 論文データを取得（40 タスク + judge.py）
python -m pip install pytest               # テスト採点に必要

python run.py --source mini --selftest     # 判定器が既存コードを follow_code と見るか確認
python run.py --source mini --reps 1       # 自作 2 タスク × 条件 A/B
python run.py --source paper --tasks P01,P05,P16 --reps 2   # 論文のタスク
python run.py --source paper --reps 2      # 論文と同じ 40 タスク × 2 条件 × 2 回 = 160 run

python summarize.py runs/runs.jsonl --by-type --runs
```

主なオプションは次のとおり。

- `--model sonnet`（既定。論文は Claude Sonnet 5.5）。`--model opus` なども指定できる。
- `--judge-model opus`（既定。論文と同じ）。`--no-conflict-judge` を付けると判定を省略する。
- `--copy-credentials`: Linux/Windows で `~/.claude/.credentials.json` によりログインしている場合に付ける。
  専用の `CLAUDE_CONFIG_DIR` にはこのファイルが無いので、これを付けてコピーする。
- `--keep-env ANTHROPIC`: `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` で認証している環境向け。
  論文はこれらを全て除去するが、除去すると認証が通らない場合に使う。
- `--keep-workspaces`: 各 run の作業ディレクトリを `runs/<run id>/workspace/` に残す。

## 注意

- 実験の性質上、`claude -p` が実際に API を呼ぶので、40 タスク × 2 条件 × 2 回はそれなりの時間と
  トークンを消費する（論文の Claude Code は 1 run あたり平均 50 秒前後）。
- 作業ディレクトリは一時ディレクトリに作る。リポジトリ内に作ると、祖先ディレクトリの CLAUDE.md が
  読み込まれて条件が汚染されるからだ。
- Claude Code のバージョンによって `claude -p` のフラグ名や stream-json の形が変わる可能性がある。
  論文は 2.1.302、このハーネスは 2.1.310 で確認している。

## 結論

**再現できた**。論文が Claude Code について報告した 3 点が、自作 2 タスク × 条件 A/B × 1 回（計 4 run）の
小規模な実験でも、同じ向きで観察された。

1. 古い CLAUDE.md がコードより優先される。一文なし（条件 A）では、判定対象の 6 選択のうち 5 選択が
   古い CLAUDE.md 側で、コード側は 0 選択だった。2 run とも run 単位でファイル側になった（論文: 86.4% がファイル側）。
2. 食い違いに気づいた上でファイルに従う。条件 A の 2 run とも、最終返答で「既存モジュールは CLAUDE.md の
   規約に反している」と明記しつつ、新規コードは CLAUDE.md に合わせた（論文: 80 run 中 79 run）。
3. ユーザーレベル CLAUDE.md の一文で反転する。一文あり（条件 B）では、ファイル側が 0 選択、コード側が 4 選択だった。
   2 run とも run 単位でコード側になり、食い違いを列挙した（論文: 94.4% がコード側、全 run で指摘）。
   既存コードの書き換えはどちらの条件でも無く、テストは全 run で通過した（論文の Claude Code と同じ）。

限界: 試行数が少ない（論文は 40 タスク × 2 回、本再現は 2 タスク × 1 回）ため、割合そのものの比較は
できない。論文の 40 タスクでの実行は下記の手順でローカルから行える。

## 再現結果（2026-10-26、Claude Code 2.1.310 + claude-sonnet-5-5、自作 2 タスク × 条件 A/B × 1 回）

`python run.py --source mini --reps 1` の結果を、`summarize.py` の出力を要約して次の表に示す。

| 条件 | ファイル側に一致 | コード側に一致 | どちらでもない | run 単位 | 食い違いの指摘 | テスト |
|---|---|---|---|---|---|---|
| A: 一文なし | 5/6 | 0/6 | 1/6 | 2/2 がファイル側 | 2/2 | 2/2 通過 |
| B: 一文あり | 0/6 | 4/6 | 2/6 | 2/2 がコード側 | 2/2 | 2/2 通過 |

小規模な実験でも、論文の Claude Code の数字（A: ファイル側 86.4%、B: コード側 94.4%、両条件で食い違いを指摘）と
同じ向きの結果が出た。

- 条件 A（M01）の最終返答の抜粋: 「The new code follows `CLAUDE.md`: namedtuple/stdlib only, `print` to
  stderr, `str.format()`. The existing modules don't follow it: `events.py`, `filter.py` and `render.py` use
  `logging`, f-strings and dataclasses. I left them alone since refactoring them is outside this task」。
  食い違いを認識した上でファイル側に従い、既存コードの方を「規約違反」として扱っている（論文 §5.2 と同じ）。
- 条件 B（M02）の最終返答の抜粋: 「Per your global instruction, I followed the existing code. The mismatches
  are: 1. Paths: `CLAUDE.md` says to use `pathlib` ... `scan.py` and `query.py` use `os.path` ... 2. Optional
  types ... 3. Tests ...」。一文によってコード側へ切り替わり、食い違いを列挙している（論文 §5.3 と同じ）。
- 「どちらでもない」は、判定器の正規表現が新規コードに一致しなかった（REC: `Digest` を namedtuple にも
  dataclass にもせず dict を返した等）か、両方の痕跡があった（LOG: `logging` を使いつつ usage 表示に
  `print` を 1 回使った）ケースだった。

### 論文の 40 タスクでの実行について

`--source paper` は、このハーネスを作ったクラウドセッションでは「外部から取得したコードの実行」として
権限ポリシーに拒否されたため、まだ実行していない。ローカルで次を実行すれば論文と同じ 160 run（Claude Code 側）になる。

```bash
./fetch_paper_data.sh
python run.py --source paper --reps 2        # 40 タスク × A/B × 2 回
python summarize.py runs/runs.jsonl --by-type
```

### ハーネス作成時に観察した注意点

- `acceptEdits` + `--allowedTools "Bash(python *)" ...` の設定では、エージェントが Bash のヒアドキュメント
  （`cat > file <<EOF`）でファイルを書こうとすると拒否される。多くの場合は Write ツールに切り替えて続行するが、
  1 回だけ、「書けたつもり」で終わって .py の変更が無い run があった。論文 Appendix A の「sandbox に拒否された
  コマンドがあれば 1 回やり直す」に合わせ、権限拒否があって .py の変更が無い run は無効とし、1 回再実行する。
