#!/bin/bash

# Example commands to run the Sudoku 4x4 evaluation script (run_sudoku.py)
# for specific puzzles using iloc arguments.
# Run these commands from the project root directory.

# --- Example 1: Run only the first 4x4 puzzle (index 0) ---
# Uses --iloc_end 1 to select puzzles from index 0 up to (but not including) 1.

echo "Running evaluation for the first puzzle (index 0)..."
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_puzzle0_$(date +%Y%m%d_%H%M%S).csv \
    --iloc_end 1 \
    --model gpt-4.1 \
    --batch_size 1

echo "--------------------"

# --- Example 2: Run specific puzzles (e.g., index 0 and 5) ---
# Uses --ilocs 0 5 to select only puzzles at index 0 and 5.

echo "Running evaluation for specific puzzles (index 0 and 5)..."
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_puzzles0_5_$(date +%Y%m%d_%H%M%S).csv \
    --ilocs 0 5 \
    --model gpt-4.1 \
    --use-planning-server \
    --batch_size 1

echo "--------------------"

# --- Example 3: Run all puzzles with gpt-4.1 and Planning Enabled ---
echo "Running evaluation for all puzzles with gpt-4.1 and Planning Enabled..."
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_gpt-4.1_planning_enabled_$(date +%Y%m%d_%H%M%S).csv \
    --model gpt-4.1 \
    --model_save_name gpt-4.1_planning_enabled \
    --use-planning-server \
    --num_empty_cells 0 5 \
    --batch_size 1

echo "--------------------"

# --- Example 4: Run all puzzles with gpt-4.1 and Planning Disabled ---
echo "Running evaluation for all puzzles with gpt-4.1 and Planning Disabled..."
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_gpt-4.1_planning_disabled_$(date +%Y%m%d_%H%M%S).csv \
    --model gpt-4.1 \
    --model_save_name gpt-4.1_planning_disabled \
    --num_empty_cells 0 5 \
    --batch_size 1

echo "--------------------"

echo "Example commands finished." 