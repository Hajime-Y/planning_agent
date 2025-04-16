# Sudoku 4x4 Benchmark Evaluation

This directory contains the script `run_sudoku.py` used to evaluate the `planning_agent`'s ability to solve 4x4 Sudoku puzzles from the `challenge_100` subset of the [SakanaAI/Sudoku-Bench](https://github.com/SakanaAI/Sudoku-Bench) dataset.

## Script Overview

`run_sudoku.py` is based on the original evaluation script from the Sudoku-Bench repository (`src/eval/run.py`). It has been modified to:

1.  Use the `planning_agent`'s `run_agent_session` function (instead of directly calling external LLM APIs).
2.  Focus exclusively on the 4x4 puzzles within the `challenge_100` dataset subset.

The script iteratively prompts the agent with the Sudoku board state and evaluates its proposed moves against the known solution.

## Prerequisites

*   **Dependencies:** Ensure you have installed the necessary Python packages listed in the project's `pyproject.toml` file, including `datasets`, `pandas`, `tqdm`, and `jinja2`. You can typically install/sync them using `uv sync`.
*   **Environment Variables:** The underlying `run_agent_session` might require environment variables (e.g., API keys for the LLM it uses). Make sure your `.env` file is configured correctly in the project root.
*   **Dependency Code:** The required code from the `Sudoku-Bench` repository must be present in the `benchmarks/sudoku_bench_deps/` directory.

## How to Run

Execute the script from the **project root directory** using `uv run` (or your preferred Python execution method).

**Basic Command:**

```bash
uv run python benchmarks/evaluation/run_sudoku.py --output_csv path/to/your/results.csv
```

**Example with Options:**

```bash
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv results/sudoku_4x4_eval_$(date +%Y%m%d_%H%M%S).csv \
    --model gpt-4o \
    --model_save_name gpt-4o-sudoku-4x4 \
    --use-planning-server \
    --n_history_turns 5 \
    --n_response_idxs 0 1 2 \
    --batch_size 1
```

## Key Command-Line Arguments

*   `--output_csv` (Required): Path where the evaluation results CSV file will be saved.
*   `--model` (Optional): Specifies the model name to be used by the `run_agent_session` (e.g., `gpt-4o`). If not provided, the agent's default model is used.
*   `--model_save_name` (Optional): The name used to identify the model in the output CSV file. Defaults to the value of `--model` or "agent_default".
*   `--use-planning-server` (Optional Flag): If included, instructs the `run_agent_session` to utilize the planning server (if available/configured).
*   `--n_history_turns` (Optional): Number of past turns to include in the prompt history. Use `-1` for full history. Default is `[-1]`.
*   `--n_response_idxs` (Optional): List of indices for running multiple trials per puzzle configuration. Default is `[0]`.
*   `--num_empty_cells` (Optional): Specifies variations by removing hints (not typically used for 4x4 evaluation). Default is `[0]`.
*   `--shuffle_seeds` (Optional): Seeds for hint removal randomization (used with `--num_empty_cells`). Default is `[0]`.
*   `--batch_size` (Optional): Number of puzzles to evaluate concurrently. Default is `1`. Use higher values with caution, especially if the agent maintains state.
*   `--max-retries` (Optional): Maximum number of retries if an agent session call fails. Default is `3`.
*   `--retry-delay` (Optional): Delay in seconds between retries. Default is `5.0`.

## Output

1.  **CSV File:** A detailed CSV file saved to the path specified by `--output_csv`. See the docstring in `run_sudoku.py` for column descriptions.
2.  **Console Output:** A summary of the evaluation results (average correct placements, solve rate) printed to the standard output upon completion. 