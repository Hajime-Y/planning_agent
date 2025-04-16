import logging
import re
from typing import Any, Dict, List, Tuple, Optional

from datasets import load_dataset
from jinja2 import Template

# Sudoku-Benchの依存コードをインポート (benchmarks/sudoku_bench_deps/ 以下に配置)
from benchmarks.sudoku_bench_deps.sudoku_ds import SudokuBoard, SudokuAction, SudokuValue
from benchmarks.sudoku_bench_deps.eval.prompts import RULE_PROMPT, BOARD_PROMPT, PREFILLED_ASSISTANT_RESPONSE
from benchmarks.sudoku_bench_deps.eval.utils import extract_action_from_response

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- プロンプトテンプレート (Jinja2) ---
# Sudoku-Bench のプロンプトをそのまま利用
RULE_PROMPT_TEMPLATE = Template(RULE_PROMPT)
BOARD_PROMPT_TEMPLATE = Template(BOARD_PROMPT)

# --- LLM 呼び出しインターフェース (仮実装) ---
def call_planning_agent_llm(messages: List[Dict[str, str]]) -> str:
    """
    planning_agent の LLM を呼び出す関数 (仮)。
    実際の LLM 連携部分に置き換える必要があります。
    """
    logger.warning("Using mock LLM response for Sudoku evaluation.")
    # ダミー応答 (例: 常に最初の空きマスに '1' を置こうとする)
    # 実際には LLM に推論させる
    # ここでは、単純な応答形式を満たすダミーを返す
    # Find first empty cell (r, c)
    last_user_message = messages[-1]['content']
    # A simple regex to find the board representation might be needed
    # For now, let's assume a simple fixed response for demonstration
    # A more sophisticated mock might try to parse the board and find an empty cell
    r, c = 1, 1 # Placeholder
    return f"Thinking... I'll place a 1 in cell r{r}c{c}. <ANSWER>r{r}c{c}: 1</ANSWER>"
    # raise NotImplementedError("LLM call function (call_planning_agent_llm) is not implemented yet.")


def load_4x4_puzzles(dataset_name: str = "challenge_100", split: str = "test") -> List[Dict[str, Any]]:
    """指定されたSudoku-Benchデータセットから4x4パズルをロードして返す"""
    try:
        dataset = load_dataset("SakanaAI/Sudoku-Bench", dataset_name, split=split)
        # Sudoku-Bench のデータセット構造に合わせて修正
        puzzles_4x4 = [
            puzzle for puzzle in dataset
            if puzzle.get('rows') == 4 and puzzle.get('cols') == 4
        ]
        logger.info(f"Loaded {len(puzzles_4x4)} 4x4 puzzles from {dataset_name}/{split}.")
        return puzzles_4x4
    except Exception as e:
        logger.error(f"Error loading dataset SakanaAI/Sudoku-Bench {dataset_name}/{split}: {e}", exc_info=True)
        return []

def parse_action(action_tuple: Optional[Tuple[str, str, str]]) -> Optional[SudokuAction]:
    """extract_action_from_responseの結果をSudokuActionに変換"""
    if not action_tuple:
        return None
    try:
        r_str, c_str, val_str = action_tuple
        # SudokuAction.from_tokens を使うのが Sudoku-Bench の実装に近い
        # <vl>, <valueZ>, <rX>, <cY> の形式のトークンリストを期待する
        tokens = [f"<vl>", f"<value{val_str}>", f"<r{r_str}>", f"<c{c_str}>"]
        return SudokuAction.from_tokens(tokens)
    except Exception as e:
        logger.error(f"Error parsing action tuple {action_tuple}: {e}", exc_info=True)
        return None

def evaluate_single_puzzle(puzzle: Dict[str, Any]) -> Dict[str, Any]:
    """planning_agent を使って 1 つの数独パズルを評価する"""
    puzzle_id = puzzle.get('puzzle_id', 'unknown_id')
    initial_board_str = puzzle.get('initial_board')
    solution_str = puzzle.get('solution')
    rows = puzzle.get('rows')
    cols = puzzle.get('cols')
    rules = puzzle.get('rules', '') # rules がない場合もある？空文字をデフォルトに
    visual_elements = puzzle.get('visual_elements') # Noneの場合もある

    if not all([initial_board_str, solution_str, isinstance(rows, int), isinstance(cols, int)]):
        logger.error(f"Skipping puzzle {puzzle_id} due to missing essential data.")
        return {
            "puzzle_id": puzzle_id,
            "status": "error",
            "error": "Missing essential puzzle data (initial_board, solution, rows, cols)",
            "num_correct_placements": 0,
            "max_rounds": 0,
            "final_solved": False,
            "final_board": None,
            "conversation": []
        }

    logger.info(f"Starting evaluation for puzzle: {puzzle_id}")

    try:
        current_board = SudokuBoard.from_ascii(initial_board_str, rows, cols)
        solution_board = SudokuBoard.from_ascii(solution_str, rows, cols)
    except Exception as e:
        logger.error(f"Error creating SudokuBoard for puzzle {puzzle_id}: {e}", exc_info=True)
        return {
            "puzzle_id": puzzle_id,
            "status": "error",
            "error": f"Failed to create SudokuBoard: {e}",
            "num_correct_placements": 0,
            "max_rounds": 0,
            "final_solved": False,
            "final_board": initial_board_str,
            "conversation": []
        }

    max_rounds = current_board.to_ascii(unfilled='.').count('.')
    num_correct_placements = 0
    conversation_history = []
    final_solved = False
    error_message = None
    status = "running" # ステータスを追加: running, completed, error

    # --- 初回プロンプト ---
    try:
        rule_prompt_rendered = RULE_PROMPT_TEMPLATE.render(
            rows=rows,
            cols=cols,
            rules=rules,
            visual_elements=visual_elements,
            initial_board=current_board.to_spaced_ascii(unfilled='.'),
        )
        conversation_history.append({"role": "user", "content": rule_prompt_rendered})
        conversation_history.append({"role": "assistant", "content": PREFILLED_ASSISTANT_RESPONSE})
    except Exception as e:
         logger.error(f"Puzzle {puzzle_id}: Error rendering initial prompt: {e}", exc_info=True)
         status = "error"
         error_message = f"Error rendering initial prompt: {e}"


    if status == "running":
        for round_num in range(max_rounds):
            round_id = round_num + 1
            logger.debug(f"Puzzle {puzzle_id}, Round {round_id}/{max_rounds}")

            # --- 盤面プロンプト生成 ---
            try:
                board_prompt_rendered = BOARD_PROMPT_TEMPLATE.render(
                    current_board=current_board.to_spaced_ascii(unfilled='.')
                )
                conversation_history.append({"role": "user", "content": board_prompt_rendered})
            except Exception as e:
                logger.error(f"Puzzle {puzzle_id}, Round {round_id}: Error rendering board prompt: {e}", exc_info=True)
                status = "error"
                error_message = f"Error rendering board prompt: {e}"
                break

            # --- planning_agent の LLM を呼び出す ---
            try:
                # 必要に応じて履歴を調整 (例: 直近N件のみ渡すなど)
                llm_response = call_planning_agent_llm(conversation_history)
                conversation_history.append({"role": "assistant", "content": llm_response})
                logger.debug(f"Puzzle {puzzle_id}, Round {round_id}: LLM Response: {llm_response[:100]}...") # 長い応答は切り詰める
            except NotImplementedError as e:
                logger.error(f"Puzzle {puzzle_id}, Round {round_id}: LLM call function not implemented: {e}")
                status = "error"
                error_message = "LLM call function not implemented"
                break
            except Exception as e:
                logger.error(f"Puzzle {puzzle_id}, Round {round_id}: Error calling LLM: {e}", exc_info=True)
                status = "error"
                error_message = f"Error calling LLM: {e}"
                break

            # --- アクション抽出 ---
            action_tuple = extract_action_from_response(llm_response)
            if not action_tuple:
                logger.warning(f"Puzzle {puzzle_id}, Round {round_id}: Invalid or no action found in response.")
                status = "completed" # アクション抽出失敗は評価終了とする
                error_message = "Invalid or no action found in response"
                break

            # --- アクション解析 & 検証 ---
            sudoku_action = parse_action(action_tuple)
            if not sudoku_action:
                logger.warning(f"Puzzle {puzzle_id}, Round {round_id}: Failed to parse action tuple: {action_tuple}")
                status = "completed"
                error_message = f"Failed to parse action tuple: {action_tuple}"
                break

            try:
                action_row, action_col = sudoku_action.coordinates[0] # (0-indexed)
                action_value_obj = sudoku_action.value # SudokuValueオブジェクト

                # 1. 既に埋まっていないかチェック
                if not current_board.get_cell(action_row, action_col).is_unfilled():
                    logger.warning(f"Puzzle {puzzle_id}, Round {round_id}: Cell ({action_row+1},{action_col+1}) is already filled.")
                    status = "completed"
                    error_message = f"Attempted to fill already filled cell r{action_row+1}c{action_col+1}"
                    break

                # 2. ルール違反でないかチェック (SudokuBoardにis_valid_placement相当のメソッドがあれば使う)
                #    Sudoku-Bench の board.py には直接的な is_valid_placement はないが、
                #    check_consistency() や get_row/col/block_values で確認できる
                #    ここでは単純化のため、正解と比較する方式を優先

                # 3. 正解かチェック
                correct_value_obj = solution_board.get_cell(action_row, action_col).value
                if action_value_obj != correct_value_obj:
                    logger.warning(f"Puzzle {puzzle_id}, Round {round_id}: Incorrect placement at ({action_row+1},{action_col+1}). Got {action_value_obj}, expected {correct_value_obj}.")
                    status = "completed"
                    error_message = f"Incorrect placement at r{action_row+1}c{action_col+1}: Got {action_value_obj}, expected {correct_value_obj}"
                    break

            except IndexError:
                 logger.error(f"Puzzle {puzzle_id}, Round {round_id}: Action coordinates ({action_row+1},{action_col+1}) out of bounds.", exc_info=True)
                 status = "error"
                 error_message = f"Action coordinates out of bounds: r{action_row+1}c{action_col+1}"
                 break
            except Exception as e:
                logger.error(f"Puzzle {puzzle_id}, Round {round_id}: Error validating action {sudoku_action}: {e}", exc_info=True)
                status = "error"
                error_message = f"Error validating action: {e}"
                break

            # --- 正解なら盤面更新 ---
            try:
                current_board.execute_action(sudoku_action)
                num_correct_placements += 1
                logger.info(f"Puzzle {puzzle_id}, Round {round_id}: Correctly placed {action_value_obj} at ({action_row+1},{action_col+1}).")
            except Exception as e:
                 logger.error(f"Puzzle {puzzle_id}, Round {round_id}: Error executing action {sudoku_action}: {e}", exc_info=True)
                 status = "error"
                 error_message = f"Error executing action: {e}"
                 break # 実行エラーなら中断

            # --- 完成判定 ---
            if '.' not in current_board.to_ascii(unfilled='.'):
                final_solved = True
                status = "completed"
                logger.info(f"Puzzle {puzzle_id}: Solved successfully!")
                break

    # ループ終了後 (max_rounds 完了 or break)
    if status == "running": # ループが正常に最後まで回った場合
        status = "completed"
        if '.' not in current_board.to_ascii(unfilled='.'):
             final_solved = True
             logger.info(f"Puzzle {puzzle_id}: Solved successfully after max rounds.")
        else:
             logger.warning(f"Puzzle {puzzle_id}: Reached max rounds ({max_rounds}) but not solved.")
             error_message = "Reached max rounds without solving"


    final_board_str = current_board.to_ascii(unfilled='.')
    logger.info(f"Finished evaluation for puzzle: {puzzle_id}. Status: {status}, Solved: {final_solved}, Correct Placements: {num_correct_placements}/{max_rounds}")

    return {
        "puzzle_id": puzzle_id,
        "status": status,
        "error": error_message,
        "num_correct_placements": num_correct_placements,
        "max_rounds": max_rounds,
        "final_solved": final_solved,
        "final_board": final_board_str,
        "conversation": conversation_history # デバッグ用に含める
    }

def run_planning_agent_sudoku_evaluation(
    dataset_name: str = "challenge_100",
    split: str = "test",
    output_file: Optional[str] = "sudoku_4x4_evaluation_results.csv"
):
    """planning_agent による Sudoku 4x4 評価を実行するメイン関数"""
    logger.info(f"Starting Sudoku 4x4 evaluation using dataset: {dataset_name}/{split}")
    puzzles_4x4 = load_4x4_puzzles(dataset_name, split)
    if not puzzles_4x4:
        logger.error("No 4x4 puzzles loaded. Aborting evaluation.")
        return

    results = []
    total_puzzles = len(puzzles_4x4)
    for i, puzzle in enumerate(puzzles_4x4):
        logger.info(f"--- Evaluating puzzle {i+1}/{total_puzzles} ---")
        result = evaluate_single_puzzle(puzzle)
        results.append(result)

    logger.info("--- Evaluation Summary ---")
    num_evaluated = len(results)
    num_errors = sum(1 for r in results if r['status'] == 'error')
    num_completed = sum(1 for r in results if r['status'] == 'completed')
    num_solved = sum(1 for r in results if r['final_solved'])

    logger.info(f"Total puzzles attempted: {num_evaluated}")
    logger.info(f"Puzzles with errors: {num_errors}")
    logger.info(f"Puzzles completed (no error): {num_completed}")
    logger.info(f"Puzzles solved successfully: {num_solved}")

    if num_completed > 0:
        accuracy = num_solved / num_completed
        logger.info(f"Accuracy (Solved / Completed): {accuracy:.2%}")
    else:
        logger.info("Accuracy: N/A (No puzzles completed without errors)")

    # 結果をCSVに保存 (オプション)
    if output_file:
        try:
            import pandas as pd
            results_df = pd.DataFrame(results)
            # conversation は巨大になる可能性があるので除くか、別途保存を検討
            if 'conversation' in results_df.columns:
                 results_df = results_df.drop(columns=['conversation'])
            results_df.to_csv(output_file, index=False)
            logger.info(f"Evaluation results saved to {output_file}")
        except ImportError:
            logger.warning("Pandas not installed. Cannot save results to CSV. Please install pandas (`uv add pandas`).")
        except Exception as e:
            logger.error(f"Failed to save results to {output_file}: {e}", exc_info=True)

    logger.info("Sudoku evaluation finished.")


if __name__ == '__main__':
    # poetry run python benchmarks/evaluation/sudoku_evaluator.py
    # または uv run python benchmarks/evaluation/sudoku_evaluator.py
    run_planning_agent_sudoku_evaluation() 