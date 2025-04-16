# 数独 4x4 ベンチマーク評価

このディレクトリには、`planning_agent` の数独解決能力を評価するためのスクリプト `run_sudoku.py` が含まれています。評価には [SakanaAI/Sudoku-Bench](https://github.com/SakanaAI/Sudoku-Bench) データセットの `challenge_100` サブセットに含まれる 4x4 パズルを使用します。

## スクリプト概要

`run_sudoku.py` は、Sudoku-Bench リポジトリのオリジナルの評価スクリプト (`src/eval/run.py`) をベースにしています。以下の点が変更されています：

1.  外部 LLM API を直接呼び出す代わりに、`planning_agent` の `run_agent_session` 関数を使用します。
2.  評価対象を `challenge_100` データセットサブセット内の 4x4 パズルのみに限定します。

このスクリプトは、数独の盤面状態を繰り返しエージェントに提示し、提案された手を既知の解答と比較して評価します。

## 前提条件

*   **依存関係:** プロジェクトの `pyproject.toml` に記載されている必要な Python パッケージ（`datasets`, `pandas`, `tqdm`, `jinja2` など）がインストールされていることを確認してください。通常、`uv sync` を使用してインストール/同期できます。
*   **環境変数:** `run_agent_session` が内部で使用する LLM の API キーなどの環境変数が必要になる場合があります。プロジェクトルートにある `.env` ファイルが正しく設定されていることを確認してください。
*   **依存コード:** `Sudoku-Bench` リポジトリから取得した必要なコードが `benchmarks/sudoku_bench_deps/` ディレクトリに存在する必要があります。

## 実行方法

**プロジェクトのルートディレクトリ** から `uv run` (または任意の Python 実行方法) を使用してスクリプトを実行します。

**基本コマンド:**

```bash
uv run python benchmarks/evaluation/run_sudoku.py --output_csv benchmarks/results/your_results.csv
```

**オプション付き実行例:**

```bash
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_$(date +%Y%m%d_%H%M%S).csv \
    --model gpt-4.1 \
    --use-planning-server \
    --n_history_turns 5 \
    --n_response_idxs 0 1 2 \
    --batch_size 1
```

## 主要なコマンドライン引数

*   `--output_csv` (必須): 評価結果を保存する CSV ファイルのパス。
*   `--model` (任意): `run_agent_session` で使用するモデル名を指定します (例: `gpt-4o`)。指定しない場合はエージェントのデフォルトモデルが使用されます。
*   `--model_save_name` (任意): 出力 CSV ファイル内でモデルを識別するための名前。指定しない場合は `--model` の値または "agent_default" が使用されます。
*   `--use-planning-server` (任意フラグ): 指定された場合、`run_agent_session` に対してプランニングサーバーの使用を指示します (利用可能/設定されている場合)。
*   `--n_history_turns` (任意): プロンプト履歴に含める過去のターン数。`-1` で完全な履歴を使用します。デフォルトは `[-1]`。
*   `--n_response_idxs` (任意): 同じパズル設定に対して複数の試行を実行するためのインデックスのリスト。デフォルトは `[0]`。
*   `--num_empty_cells` (任意): ヒントを削除することによるバリエーションを指定します (通常 4x4 評価では使用しません)。デフォルトは `[0]`。
*   `--shuffle_seeds` (任意): ヒント削除のランダム化のためのシード (`--num_empty_cells` と共に使用)。デフォルトは `[0]`。
*   `--iloc_start` (任意): 評価対象とする 4x4 パズルの開始インデックス (0始まり)。デフォルトは `0`。
*   `--iloc_end` (任意): 評価対象とする 4x4 パズルの終了インデックス (このインデックス自体は含まない)。デフォルトは全パズル。
*   `--ilocs` (任意): 評価対象とする 4x4 パズルのインデックスを個別に指定 (スペース区切り)。これを指定すると `--iloc_start`/`--iloc_end` は無視されます。
*   `--batch_size` (任意): 同時に評価するパズルの数。デフォルトは `1`。エージェントが状態を持つ場合は注意して使用してください。
*   `--max-retries` (任意): エージェントセッションの呼び出しが失敗した場合の最大リトライ回数。デフォルトは `3`。
*   `--retry-delay` (任意): リトライ間の遅延時間 (秒)。デフォルトは `5.0`。

## 出力

1.  **CSV ファイル:** `--output_csv` で指定されたパスに詳細な CSV ファイルが保存されます。列の説明については `run_sudoku.py` の docstring を参照してください。
2.  **コンソール出力:** 完了時に、評価結果の概要 (平均正解配置数、解決率) が標準出力に出力されます。 