#!/bin/bash

# TravelPlanner Sole-Planning ベンチマーク実行サンプルスクリプト
# このスクリプトは planning_agent リポジトリのルートディレクトリから実行してください

# ----------------------------------------------------------------
# 環境セットアップ（必要に応じてコメントを外して実行）
# ----------------------------------------------------------------
# uv sync --no-editable --dev
# huggingface-cli login

# ----------------------------------------------------------------
# ベンチマーク実行コマンド例
# ----------------------------------------------------------------

# バリデーションセットでの実行例（1サンプルに制限）
uv run python benchmarks/travel_planner/sole_planning.py \
    --model_name gpt-4.1 \
    --set_type validation \
    --output_dir benchmarks/travel_planner/results/$(date +%Y%m%d_%H%M%S) \
    --limit 1

# バリデーションセットでの実行例（全サンプル）
# uv run python benchmarks/travel_planner/sole_planning.py \
#     --model_name gpt-4.1 \
#     --set_type validation \
#     --output_dir benchmarks/travel_planner/results/$(date +%Y%m%d_%H%M%S)

# テストセットでの実行例
# uv run python benchmarks/travel_planner/sole_planning.py \
#     --model_name gpt-4.1 \
#     --set_type test \
#     --output_dir benchmarks/travel_planner/results/$(date +%Y%m%d_%H%M%S)

# プランニングサーバーを使用した実行例
# uv run python benchmarks/travel_planner/sole_planning.py \
#     --model_name gpt-4.1 \
#     --set_type validation \
#     --output_dir benchmarks/travel_planner/results/$(date +%Y%m%d_%H%M%S) \
#     --use_planning_server

# ----------------------------------------------------------------
# 評価コマンド例
# ----------------------------------------------------------------
# uv run python external/TravelPlanner/postprocess/evaluate.py \
#     --result_dir benchmarks/travel_planner/results/YOUR_RESULT_FOLDER \
#     --model_name "gpt-4.1_direct_sole-planning" 