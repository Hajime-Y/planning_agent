# Sudoku-Bench 実装調査と Planning Agent による評価ガイド

## 1. はじめに

このドキュメントは、[SakanaAI/Sudoku-Bench](https://github.com/SakanaAI/Sudoku-Bench) データセットを利用して、`planning_agent` (この AI アシスタント) 自身の数独解決能力を評価するための技術的な指針を提供します。Issue #36 のタスクに基づき、特に `challenge_100` データセット内の 4x4 パズルの評価方法に焦点を当てます。

**重要な注意点:** このアプローチは、`Sudoku-Bench` リポジトリに含まれる `src/eval/run.py` スクリプト (外部 LLM の評価用) を直接使用するものではありません。`planning_agent` 自身が評価ループを実行するように、必要なロジックを `planning_agent` 内に実装します。

## 2. Sudoku-Bench データセットの概要

`Sudoku-Bench` は、数独パズルのデータセットであり、HuggingFace Hub ([SakanaAI/Sudoku-Bench](https://huggingface.co/datasets/SakanaAI/Sudoku-Bench)) で公開されています。様々なサイズや難易度のパズルが含まれており、LLM の論理的推論能力を測るベンチマークとして利用できます。

データセットの各要素には、主に以下の情報が含まれます:

*   `puzzle_id`: パズルの一意な識別子
*   `initial_board`: パズルの初期盤面 (ASCII 文字列)
*   `solution`: パズルの完成盤面 (ASCII 文字列)
*   `rows`, `cols`: 盤面の行数と列数
*   `rules`: パズルのルール (標準的な数独ルールなど)
*   `visual_elements`: 視覚的な制約 (ケージなど、一部のパズルに存在)

## 3. Planning Agent による評価プロセス

`planning_agent` 自身が 4x4 数独パズルを解く能力を評価するためのプロセスは以下のようになります。

1.  **データ準備:**
    *   `datasets` ライブラリを使用して、HuggingFace Hub から `SakanaAI/Sudoku-Bench` の `challenge_100` subset をロードします。
    *   ロードしたデータセットから `rows == 4` かつ `cols == 4` の条件で 4x4 パズルのみをフィルタリングします。
2.  **評価ループの実行:**
    *   フィルタリングした各 4x4 パズルに対して、以下のステップを繰り返します。
        *   **(a) プロンプト生成:** パズルの初期盤面、ルール説明 (後述のプロンプト設計参照)、および現在の盤面状況を `planning_agent` の LLM が理解できる形式のプロンプトに整形します。
        *   **(b) LLM 推論:** `planning_agent` 内部の LLM (現在対話している LLM) に生成したプロンプトを入力し、「次の一手（どのマスにどの数字を置くか）」を推論させます。応答形式は `<ANSWER>r<row>c<col>: <value></ANSWER>` (例: `<ANSWER>r1c2: 3</ANSWER>`) のような形式を期待します。
        *   **(c) アクション検証:** LLM の応答からアクション (行、列、値) を抽出します。抽出できない、または形式が不正な場合はエラーとして処理します。
        *   **(d) 正当性チェック:** 抽出したアクションが数独のルール (行、列、ブロック内で数字が重複しないか) に違反していないか、また既に数字が埋まっているマスへの配置でないかなどを検証します。ルール違反の場合はエラーとします。
        *   **(e) 正解チェック:** (d) をクリアした場合、その手がデータセットの `solution` と照らし合わせて正しいかを確認します。間違っている場合は、そのパズルでの試行を終了します。
        *   **(f) 盤面更新:** (e) で正解だった場合、`planning_agent` が管理する現在の盤面状態を更新します。
        *   **(g) 終了判定:** 盤面が完全に埋まったら (完成)、そのパズルは成功として終了します。
3.  **結果集計:**
    *   各パズルについて、成功したか失敗したか、何手まで正しく進められたか、最終的な盤面などを記録します。
    *   全 4x4 パズルに対する成功率や平均正解手数などを計算します。

## 4. 実装方針 (`planning_agent` 内)

`planning_agent` のコードベース内に、上記の評価プロセスを実行するための新しいモジュールまたは関数を実装します。

### 4.1. 必要なライブラリ

*   `datasets`: HuggingFace Hub からデータセットをロードするために必要です。
    ```bash
    # planning_agent の環境に追加
    uv add datasets
    ```
*   (任意) `Sudoku-Bench` リポジトリ: `prompts.py`, `utils.py`, `sudoku-ds` ライブラリは、実装の参考または一部再利用のためにローカルにクローンしておくと便利です。ただし、必須ではありません。主要なロジックを `planning_agent` 内に再実装することも可能です。
    *   [src/eval/prompts.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/prompts.py): プロンプトテンプレート
    *   [src/eval/utils.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/utils.py): アクション抽出などのユーティリティ
    *   [src/sudoku_ds/](https://github.com/SakanaAI/Sudoku-Bench/tree/main/src/sudoku_ds): 盤面・アクション表現クラス

### 4.2. 実装のポイント

*   **データローダー:** `challenge_100` をロードし、4x4 パズルをフィルタリングする関数を実装します。
*   **評価コア関数:** 1つのパズルを受け取り、上記の評価ループ (3-2) を実行し、結果 (成功/失敗、手数など) を返す関数を実装します。この関数内部で `planning_agent` の LLM 推論呼び出しが行われます。
*   **プロンプト設計:**
    *   `planning_agent` の LLM に数独のルールと盤面状態を効果的に伝えるプロンプトを設計します。
    *   **重要:** `Sudoku-Bench` の評価方法に準拠するため、[src/eval/prompts.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/prompts.py) 内の `RULE_PROMPT` (初回用) と `BOARD_PROMPT` (2回目以降用) の内容を **正確に参照・利用することが強く推奨されます。** これには、ルール説明、盤面サイズ、視覚要素の記述方法、そして特に **応答形式 (`<ANSWER>rXcY: Z</ANSWER>`) の指示** が含まれます。
    *   `jinja2` などのテンプレートエンジンを使って、データセットの `rules`, `rows`, `cols`, `visual_elements` や現在の盤面状況に応じて動的にプロンプトを生成するのが良いでしょう。
*   **盤面管理:** 評価中の現在の盤面状態を保持・更新するためのデータ構造が必要です。`Sudoku-Bench` の [src/sudoku_ds/board.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/sudoku_ds/board.py) の `SudokuBoard` クラスを参考にしたり、流用したりするのが効率的です。
*   **アクション解析と検証:**
    *   LLM の応答文字列 (例: `Thinking...\n<ANSWER>r1c2: 3</ANSWER>`) から `<ANSWER>` タグ内のアクション (`r1c2: 3`) を正確に抽出するロジックが必要です。[src/eval/utils.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/utils.py) の `extract_action_from_response` が参考になります。
    *   抽出したアクションの形式チェック、ルール違反チェック、正解チェックを行う必要があります。[src/sudoku_ds/action.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/sudoku_ds/action.py) の `SudokuAction` クラスや `SudokuBoard` クラスのメソッド (`is_valid_move` に相当するロジック、`get_cell` を使った正解比較など) を参照・利用することを推奨します。
*   **結果の記録:** 評価結果を格納するためのデータ構造 (例: リストや Pandas DataFrame) と、最終的にファイル (CSV など) に保存する処理を実装します。

### 4.3. 実装イメージ (概念的なコード)

```python
from datasets import load_dataset
# import jinja2 # プロンプト生成用
# from planning_agent.llm import call_planning_agent_llm # planning_agentのLLM呼び出し関数 (仮)
# # Sudoku-Bench から関連クラス・関数をインポートするか、planning_agent内に実装/移植
# from planning_agent.sudoku_utils import (
#     SudokuBoard, SudokuAction,
#     extract_action_from_response, # utils.py 参照
#     # render_board # 盤面表示用 (自作 or SudokuBoard.to_ascii)
# )

# --- 定数 (prompts.py 参照) ---
# RULE_PROMPT_TEMPLATE = jinja2.Template(\"\"\"... prompts.py の RULE_PROMPT の内容 ...\"\"\")
# BOARD_PROMPT_TEMPLATE = jinja2.Template(\"\"\"... prompts.py の BOARD_PROMPT の内容 ...\"\"\")
# PREFILLED_ASSISTANT_RESPONSE = \"\"\"... prompts.py の PREFILLED_ASSISTANT_RESPONSE ...\"\"\" # 初回応答用

def load_4x4_puzzles(dataset_name=\"challenge_100\") -> list[dict]:
    \"\"\"指定されたSudoku-Benchデータセットから4x4パズルをロードして返す\"\"\"
    try:
        dataset = load_dataset("SakanaAI/Sudoku-Bench", dataset_name, split="test")
        puzzles_4x4 = [puzzle for puzzle in dataset if puzzle['rows'] == 4 and puzzle['cols'] == 4]
        print(f"Loaded {len(puzzles_4x4)} 4x4 puzzles from {dataset_name}.")
        return puzzles_4x4
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return []

# def format_sudoku_prompt(...): # jinja2を使う方が柔軟性が高い
#     # ... RULE_PROMPT_TEMPLATE や BOARD_PROMPT_TEMPLATE を使って生成 ...

def evaluate_single_puzzle(puzzle: dict) -> dict:
    \"\"\"planning_agent を使って 1 つの数独パズルを評価する\"\"\"
    initial_board_str = puzzle['initial_board']
    solution_str = puzzle['solution']
    rules = puzzle['rules']
    rows = puzzle['rows']
    cols = puzzle['cols']
    visual_elements = puzzle.get('visual_elements') # Noneの場合もある

    # SudokuBoard を使う場合 (推奨)
    try:
        current_board = SudokuBoard.from_ascii(initial_board_str, rows, cols)
        solution_board = SudokuBoard.from_ascii(solution_str, rows, cols)
    except Exception as e:
        print(f\"Error creating SudokuBoard for {puzzle['puzzle_id']}: {e}\")
        return { \"puzzle_id\": puzzle['puzzle_id'], \"error\": str(e) } # エラー情報を返す

    max_rounds = current_board.to_ascii(unfilled='.').count('.')
    num_correct_placements = 0
    conversation_history = []
    final_solved = False

    # --- 初回プロンプト ---
    # rule_prompt_rendered = RULE_PROMPT_TEMPLATE.render(...) # Jinja2 でレンダリング
    # conversation_history.append({\"role\": \"user\", \"content\": rule_prompt_rendered})
    # conversation_history.append({\"role\": \"assistant\", \"content\": PREFILLED_ASSISTANT_RESPONSE})

    for round_num in range(max_rounds):
        # --- 盤面プロンプト生成 ---
        # board_prompt_rendered = BOARD_PROMPT_TEMPLATE.render(current_board=current_board.to_spaced_ascii(unfilled='.'))
        # conversation_history.append({\"role\": \"user\", \"content\": board_prompt_rendered})

        # --- planning_agent の LLM を呼び出す ---
        # input_messages = conversation_history[-N:] # 必要に応じて履歴を含める
        # llm_response = call_planning_agent_llm(input_messages) # 仮の関数呼び出し
        llm_response = f\"Thinking... <ANSWER>r{round_num+1}c1: {(round_num % 4) + 1}</ANSWER>\" # 仮の応答 (デバッグ用)
        conversation_history.append({\"role\": \"assistant\", \"content\": llm_response})

        # --- アクション抽出 (utils.py 参照) ---
        action_tuple = extract_action_from_response(llm_response) # 例: (row, col, val) or None
        if not action_tuple:
            print(f\"Puzzle {puzzle['puzzle_id']}, Round {round_num+1}: Invalid action format in response.\")
            break

        # --- アクション検証 (SudokuAction, SudokuBoard 参照) ---
        try:
            # SudokuAction に変換 (座標は 0-indexed に注意)
            r_str, c_str, val_str = action_tuple
            sudoku_action = SudokuAction.from_tokens([f\"<vl>\", f\"<value{val_str}>\", f\"<r{r_str}>\", f\"<c{c_str}>\"])
            action_row, action_col = sudoku_action.coordinates[0] # (0-indexed)
            action_value = sudoku_action.value.value

            # 既に埋まっていないか & ルール違反でないか (SudokuBoard内にチェックロジックがあると良い)
            if not current_board.is_valid_placement(action_row, action_col, action_value):
                 print(f\"Puzzle {puzzle['puzzle_id']}, Round {round_num+1}: Invalid move by rule or already filled.\")
                 break

            # 正解かチェック
            correct_value = solution_board.get_cell(action_row, action_col).value.value
            if action_value != correct_value:
                print(f\"Puzzle {puzzle['puzzle_id']}, Round {round_num+1}: Incorrect placement ({action_value} vs {correct_value}).\")
                break

        except Exception as e:
            print(f\"Puzzle {puzzle['puzzle_id']}, Round {round_num+1}: Error validating action {action_tuple}: {e}\")
            break

        # --- 正解なら盤面更新 (SudokuBoard 参照) ---
        try:
            current_board.execute_action(sudoku_action)
            num_correct_placements += 1
        except Exception as e:
             print(f\"Puzzle {puzzle['puzzle_id']}, Round {round_num+1}: Error executing action {sudoku_action}: {e}\")
             break # 実行エラーなら中断

        # --- 完成判定 ---
        if '.' not in current_board.to_ascii(unfilled='.'):
            final_solved = True
            print(f\"Puzzle {puzzle['puzzle_id']}: Solved!\")
            break

    return {
        \"puzzle_id\": puzzle['puzzle_id'],
        \"num_correct_placements\": num_correct_placements,
        \"max_rounds\": max_rounds,
        \"final_solved\": final_solved,
        \"final_board\": current_board.to_ascii(unfilled='.'), # 結果は '.' 埋め形式
        \"conversation\": conversation_history # オプション
    }

def run_planning_agent_sudoku_evaluation():
    \"\"\"planning_agent による Sudoku 4x4 評価を実行するメイン関数\"\"\"
    puzzles_4x4 = load_4x4_puzzles()
    if not puzzles_4x4:
        return

    results = []
    for puzzle in puzzles_4x4:
        result = evaluate_single_puzzle(puzzle)
        results.append(result)
        # 必要に応じて途中結果を表示
        print(f"Evaluated Puzzle {result['puzzle_id']}: Solved={result['final_solved']}, Correct={result['num_correct_placements']}/{result['max_rounds']}")

    # 結果を集計して表示・保存 (例: Pandas DataFrame を使う)
    # import pandas as pd
    # results_df = pd.DataFrame(results)
    # print(results_df)
    # print(f"Overall Accuracy: {results_df['final_solved'].mean():.2f}")
    # results_df.to_csv("planning_agent_sudoku_4x4_results.csv", index=False)
    print("Evaluation finished.")

# --- 実行 ---
# if __name__ == \"__main__\": # main.py などから呼び出す想定
#    run_planning_agent_sudoku_evaluation()
```
*注意:* 上記は概念的なコードであり、`planning_agent` の実際の LLM 呼び出し方法や、`Sudoku-Bench` から流用・参考にすべきユーティリティ関数/クラス (`extract_action_from_response`, `SudokuBoard`, `SudokuAction`, プロンプトテンプレート等) の **具体的な実装やインポートは別途必要です。**

## 5. まとめ

*   `planning_agent` 自身の数独解決能力を評価するには、`Sudoku-Bench` のデータセット (4x4 パズル) を使用し、`planning_agent` 内部で評価ループを実装する必要があります。
*   `Sudoku-Bench` リポジトリの `src/eval/run.py` は **使用しません**。
*   実装には、データロード (`datasets` ライブラリ)、LLM 推論呼び出し、プロンプト設計、アクション解析、盤面管理、結果集計のロジックが必要です。
*   `Sudoku-Bench` の既存コード (特に [src/eval/prompts.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/prompts.py), [src/eval/utils.py](https://github.com/SakanaAI/Sudoku-Bench/blob/main/src/eval/utils.py), [src/sudoku_ds/](https://github.com/SakanaAI/Sudoku-Bench/tree/main/src/sudoku_ds)) は、**プロンプトの内容、アクション抽出、盤面管理などの実装において正確に参照・利用することを強く推奨します。** 