"""
Evaluate planning_agent on Sudoku 4x4 puzzles using run_agent_session.

This script is based on Sudoku-Bench/src/eval/run.py (commit hash might be relevant).
It evaluates the planning_agent's ability to solve 4x4 Sudoku puzzles
from the challenge_100 dataset subset.

The agent is called repeatedly:
  1) Provide an initial puzzle prompt (rule prompt).
  2) Agent responds with a single forced placement (e.g., <ANSWER>r3c6: 5</ANSWER>).
  3) We check if that placement is valid and correct based on the puzzle's known solution.
  4) If correct, we update the board and provide the new board state for the next turn.
  5) Continue until the puzzle is solved, an incorrect placement is made,
     or the agent fails to respond correctly.

Target Dataset: SakanaAI/Sudoku-Bench, challenge_100 subset, filtered for 4x4 puzzles.

Example Usage (from project root):
----------------------------------
# Ensure necessary dependencies are installed (datasets, pandas, tqdm, jinja2)
# Ensure .env file is set up if required by run_agent_session

Example Usage:
--------------
uv run python benchmarks/evaluation/run_sudoku.py \
    --output_csv benchmarks/results/sudoku_4x4_eval_$(date +%Y%m%d_%H%M%S).csv \
    --model gpt-4.1 \
    --use-planning-server \
    --n_history_turns 5 \
    --batch_size 1

Output:
-------
A CSV file with columns (similar to original run.py):
[
    "data_source",      # Always "challenge_100"
    "puzzle_id",
    "model",            # Model name used for saving (from --model_save_name or --model)
    "num_empty_cells",  # Number of hints removed (usually 0 for 4x4)
    "shuffle_seed",     # Seed for hint removal (usually 0 for 4x4)
    "n_response_idx",   # Trial index for the same puzzle configuration
    "n_history_turns",  # History turns setting used (e.g., 5 or -1 for full)
    "setting",          # String combining history setting
    "initial_board",    # The initial board state given to the agent
    "conversation",     # JSON dump of the full conversation history
    "num_rounds",       # Number of rounds executed
    "num_correct_placements", # Number of correct moves made by the agent
    "final_solved",     # 1 if solved correctly, 0 otherwise
    "final_board",      # Final board state after evaluation ended
]

Puzzle Selection Arguments:
-------------------------
*   `--iloc_start`: Start index of 4x4 puzzles to evaluate (default: 0)
*   `--iloc_end`: End index of 4x4 puzzles to evaluate (exclusive, default: all)
*   `--ilocs`: Specific indices (plural) of 4x4 puzzles to evaluate (overrides start/end)

Plus a summary of average correctness/final-solved rates printed to stdout.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Union

import datasets
import jinja2
import pandas as pd
from tqdm import tqdm

try:
    from front_agents.generic_task_agent import run_agent_session, AgentSessionResult
except ImportError as e:
    print(f"Error importing agent session function: {e}. Ensure PYTHONPATH or execution context is correct.", file=sys.stderr)
    sys.exit(1)

from benchmarks.sudoku_bench_deps.eval.prompts import (
    BOARD_PROMPT,
    PREFILLED_ASSISTANT_RESPONSE,
    RULE_PROMPT,
)
from benchmarks.sudoku_bench_deps.eval.utils import (
    extract_action_from_response,
    pretty_print_visual_elements,
    random_fill_hints,
)
from benchmarks.sudoku_bench_deps.sudoku_ds import (
    SudokuAction,
    SudokuBoard,
    SudokuValue,
    SudokuCell,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def call_agent_session(
    args: argparse.Namespace,
    messages: Union[str, List[Dict]],
    model: Optional[str] = None,
    use_planning_server: Optional[bool] = None,
) -> Optional[str]:
    """
    Specify the input to call run_agent_session and perform retry processing.
    If successful, return the final response string from the agent.
    """
    attempt = 0
    while attempt < args.max_retries:
        try:
            agent_result: Optional[AgentSessionResult] = await run_agent_session(
                model=model,
                user_input=messages,
                use_planning_server=use_planning_server,
            )

            output_text = agent_result.final_output
            return output_text

        except Exception as e:
            attempt += 1
            if attempt == args.max_retries:
                print(f"Failed after {args.max_retries} attempts for request. {e}")
                return None
            # Add small delay between retries
            await asyncio.sleep(args.retry_delay)


async def process_one(
    args: argparse.Namespace,
    request: Dict,
    model: str,
    use_planning_server: bool,
) -> Dict:
    # Load data
    rules = request["rules"]
    current_board_ascii = request["initial_board"]
    solution_ascii = request["solution"]
    rows = request["rows"]
    cols = request["cols"]
    visual_elements = request["visual_elements"]
    if pd.isna(visual_elements) or visual_elements == "":
        visual_elements = None
    n_history_turns = request["n_history_turns"]

    # Construct setting string
    settings = []
    if n_history_turns == -1:
        settings.append("full-history")
    else:
        assert n_history_turns >= 0
        settings.append(f"{n_history_turns}-history-turns")
    if len(settings) == 0:
        setting = "default"
    else:
        setting = "_".join(settings)

    # Pretty print visual elements
    if visual_elements is None:
        pretty_visual_elements = None
    else:
        visual_elements = json.loads(visual_elements)
        pretty_visual_elements = pretty_print_visual_elements(visual_elements)

    # Construct boards
    solution_board = SudokuBoard.from_ascii(solution_ascii, rows, cols)
    current_board = SudokuBoard.from_ascii(current_board_ascii, rows, cols)
    max_rounds = current_board.to_ascii(unfilled=".").count(".")

    # Initial conversation
    rule_prompt = jinja2.Template(RULE_PROMPT).render(
        rows=rows,
        cols=cols,
        rules=rules,
        pretty_visual_elements=pretty_visual_elements,
    )
    # `history_conversation`` is for recording
    # Actual input conversation will be constructed before calling API
    history_conversation: List[Dict] = [
        {"role": "user", "content": rule_prompt},
        {"role": "assistant", "content": PREFILLED_ASSISTANT_RESPONSE}
    ]

    num_correct_placements = 0
    for round_idx in range(max_rounds):
        round_str = f"Round {round_idx + 1} / {max_rounds}"

        ##################
        ## Get response ##
        ################## 

        # Construct user prompt describing the current board
        board_prompt = jinja2.Template(BOARD_PROMPT).render(
            current_board=current_board.to_spaced_ascii(unfilled="."),
        )
        history_conversation.append({"role": "user", "content": board_prompt})

        # Construct input conversation
        # If full history, include all history turns
        if n_history_turns == -1:
            input_conversation = [
                {"role": message["role"], "content": message["content"]}
                for message in history_conversation
            ]
        # Otherwise
        # - First two prompts are fixed (rule prompt and prefilled assistant response)
        # - Last prompt is the current board
        # - In between, we add the most recent history turns
        else:
            input_conversation = [
                {"role": message["role"], "content": message["content"]}
                for message in \
                    history_conversation[:2] \
                    + history_conversation[2:-1][-2*n_history_turns:] \
                    + history_conversation[-1:]
            ]

        # Call Agent Session
        assistant_response = await call_agent_session(
            args=args,
            model=model,
            use_planning_server=use_planning_server,
            messages=input_conversation,
        )

        # Teriminate if no response
        if not assistant_response:
            print(f"{round_str}. No response from agent session.")
            break

        # Update conversation
        history_conversation.append({"role": "assistant", "content": assistant_response})

        #################################
        ## Solution-independent checks ##
        #################################

        # Extract action from response
        action = extract_action_from_response(assistant_response)
        # Terminate if no action found
        if not action:
            print(f"[Fail] {round_str}. No valid action found in response.")
            break

        # Convert to SudokuAction
        try:
            r_str, c_str, val_str = action
            sudoku_action = SudokuAction.from_tokens([
                "<vl>", f"<value{val_str}>", f"<r{r_str}>", f"<c{c_str}>"
            ])
        # Terminate if action parsing fails
        except Exception as e:
            print(f"[Fail] {round_str}. Error parsing action: {e}.")
            break

        # Update board state
        try:
            current_board.execute_action(sudoku_action)
        # Terminate if action execution fails
        except Exception as e:
            print(f"[Fail] {round_str}. Error executing action: {e}")
            break

        ###############################
        ## Solution-dependent checks ##
        ###############################

        # Check correctness
        action_row, action_col = sudoku_action.coordinates[0]
        ref = solution_board.get_cell(action_row, action_col).value.value
        hyp = sudoku_action.value.value 
        if hyp == ref:
            print(f"[Pass] {round_str}.")
            num_correct_placements += 1
        # Terminate if incorrect placement
        else:
            print(f"[Fail] {round_str}. Incorrect placement at {action_row}, {action_col}.")
            break

        # Teriminate if all cells are filled
        if '.' not in current_board.to_ascii(unfilled="."):
            print(f"[Pass] {round_str}. All cells filled.")
            break

    ##########################
    ## Final solution match ##
    ##########################

    # Check if solution is correct
    final_board_ascii = current_board.to_ascii(unfilled=".")
    final_solved = 1 if (final_board_ascii == solution_ascii) else 0

    return {
        # From input
        "data_source": args.dataset,
        "puzzle_id": request["puzzle_id"],
        "model": args.model_save_name if args.model_save_name else model,
        "num_empty_cells": request["num_empty_cells"],
        "shuffle_seed": request["shuffle_seed"],
        "n_response_idx": request["n_response_idx"],
        "n_history_turns": n_history_turns,
        "setting": setting,
        "initial_board": request["initial_board"],
        # From output
        "conversation": json.dumps(history_conversation),
        "num_rounds": round_idx + 1,
        "num_correct_placements": num_correct_placements,
        "final_solved": final_solved,
        "final_board": final_board_ascii,
    }


async def process_batch(
    args: argparse.Namespace,
    requests: List[Dict],
    model: str,
    use_planning_server: bool,
    batch_size: int = 1
) -> List[Dict]:
    semaphore = asyncio.Semaphore(batch_size)
    async def process_with_semaphore(request):
        async with semaphore:
            return await process_one(
                args=args,
                request=request,
                model=model,
                use_planning_server=use_planning_server,
            )
    
    tasks = [process_with_semaphore(request) for request in requests]
    outputs = []
    
    # Process requests with progress bar
    with tqdm(total=len(tasks), desc="Processing requests") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            outputs.append(result)
            pbar.update(1)
    
    return outputs


def construct_request(
    puzzle_id: str,
    author: str,
    rules: str,
    visual_elements: Optional[str],
    initial_board: str,
    solution: str,
    rows: int,
    cols: int,
    num_empty_cells: int,
    shuffle_seed: Optional[int],
    n_response_idx: int,
    n_history_turns: int,
) -> Optional[Dict]:
    # Fill hints if needed
    if num_empty_cells > 0:
        initial_board = random_fill_hints(
            initial_board,
            solution,
            num_empty_cells,
            shuffle_seed,
        )
        if initial_board is None:
            return None
    return {
        "puzzle_id": puzzle_id,
        "author": author,
        "rules": rules,
        "visual_elements": visual_elements,
        "initial_board": initial_board,
        "solution": solution,
        "rows": rows,
        "cols": cols,
        "num_empty_cells": num_empty_cells,
        "shuffle_seed": shuffle_seed,
        "n_response_idx": n_response_idx,
        "n_history_turns": n_history_turns,
    }
    

def main():
    parser = argparse.ArgumentParser(description="Evaluate Agent on Sudoku 4x4 puzzles in a multi-round manner.")

    # Filepaths
    parser.add_argument("--output_csv", type=str, required=True,
                        help="Output CSV path.")

    # Subset of puzzles to evaluate
    parser.add_argument("--iloc_start", type=int, default=0,
                        help="Start index of puzzles to evaluate.")
    parser.add_argument("--iloc_end", type=int, default=None,
                        help="End index of puzzles to evaluate (exclusive).")
    parser.add_argument("--ilocs", type=int, nargs="+",
                        help="Specific puzzle indices to evaluate. Overrides start/end.")

    # Eval setting
    # The number of evaluations for each puzzle is the product of the following four arguments.
    parser.add_argument("--num_empty_cells", type=int, nargs="+", default=[0, 5, 10],
                        help="Number of empty cells in the intial board after hint fill in random cells. "
                             "0 means the original board.")
    parser.add_argument("--shuffle_seeds", type=int, nargs="+", default=[0],
                        help="Shuffle seeds for the random hint fill. Only used if num_empty_cells > 0.")
    parser.add_argument("--n_response_idxs", type=int, nargs="+", default=[0],
                        help="If you want to run multiple trials per puzzle/hint/seed. E.g., [0,1,2,3,4] for 5 runs.")
    parser.add_argument("--n_history_turns", type=int, nargs="+", default=[5],
                        help="Number of history turns to include in each LLM prompt. -1 means full history.")

    # Agent/Model Settings
    parser.add_argument("--model", type=str, default=None,
                        help="Model name to use for the agent session (e.g., gpt-4.1).")
    parser.add_argument("--model_save_name", type=str, default=None,
                        help="Model name to save in results. If not provided, use --model or agent default.")
    parser.add_argument("--use-planning-server", action='store_true',
                        help="Use the planning server within the agent session.")

    # Execution Settings
    parser.add_argument("--batch_size", type=int, default=1,
                        help="Batch size for parallel processing (use with caution if agent has state).")
    parser.add_argument("--max_retries", type=int, default=3,
                        help="Max retries for agent session calls.")
    parser.add_argument("--retry_delay", type=float, default=5.0,
                        help="Delay (in second) between retries.")

    args = parser.parse_args()

    # Sanity check
    assert args.num_empty_cells != [0] or len(args.shuffle_seeds) == 1, \
        "shuffle_seed is only used when providing hints (i.e. num_empty_cells > 0)."

    # dataset 名を args に追加 (process_one で参照するため)
    args.dataset = "challenge_100"

    # Load puzzle
    dataset = datasets.load_dataset("SakanaAI/Sudoku-Bench", args.dataset, split="test")
    # filter メソッドで 4x4 パズルを抽出
    dataset = dataset.filter(lambda example: example.get('rows') == 4 and example.get('cols') == 4)

    # Use a subset of puzzles if specified
    if args.ilocs is not None:
        ilocs = args.ilocs
    else:
        end_idx = args.iloc_end if args.iloc_end is not None else len(dataset)
        ilocs = range(args.iloc_start, end_idx)
    puzzle_rows = [dataset[i] for i in ilocs]
    print(f"Number of puzzles to evaluate: {len(puzzle_rows)}")

    # Construct requests
    requests = []
    for puzzle_row in puzzle_rows:
        for nhist in args.n_history_turns:
            for ne in args.num_empty_cells:
                for sseed in args.shuffle_seeds:
                    for nr_idx in args.n_response_idxs:
                        request = construct_request(
                            puzzle_id=puzzle_row["puzzle_id"],
                            author=puzzle_row["author"],
                            rules=puzzle_row["rules"],
                            visual_elements=puzzle_row["visual_elements"],
                            initial_board=puzzle_row["initial_board"],
                            solution=puzzle_row["solution"],
                            rows=puzzle_row["rows"],
                            cols=puzzle_row["cols"],
                            num_empty_cells=ne,
                            shuffle_seed=sseed,
                            n_response_idx=nr_idx,
                            n_history_turns=nhist,
                        )
                        if request is not None:
                            requests.append(request)
    print(f"Number of requests to process: {len(requests)}")

    # Process batch
    all_results = asyncio.run(process_batch(
        args=args,
        batch_size=args.batch_size,
        requests=requests,
        model=args.model,
        use_planning_server=args.use_planning_server,
    ))

    # Convert results to DataFrame
    res_df = pd.DataFrame(all_results)
    if len(res_df) == 0:
        print("No results to save. Possibly no puzzles or an error occurred.")
        return

    # Print summary
    # We'll measure average number of correct placements and fraction of puzzles solved.
    group_cols = ["num_empty_cells", "setting", "model"]
    summary = (
        res_df
        .groupby(group_cols)
        .agg({
            "num_correct_placements": "mean",
            "final_solved": "mean"
        })
        .reset_index()
    )
    with pd.option_context("display.max_rows", None, "display.precision", 2):
        print(summary)

    # Save results to CSV
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    res_df.to_csv(args.output_csv, index=False)
    print(f"\nResults saved to {args.output_csv}")


if __name__ == "__main__":
    # .env ファイル読み込み
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print(".env file loaded if found.")
    except ImportError:
        print("python-dotenv not installed, skipping .env file loading.")

    main()