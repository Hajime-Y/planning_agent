"""
MCPサーバー実装

このモジュールは、FastMCPライブラリを使用してPlanning AgentシステムのMCPサーバーを実装します。
クライアントからのリクエストを受け付け、適切なツール関数を呼び出します。
"""

import sys
import os

# このファイルのディレクトリを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトルートディレクトリを取得 (mcp_interface の親ディレクトリ)
project_root = os.path.dirname(current_dir)
# sys.path にプロジェクトルートを追加 (既に追加されていない場合)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
from typing import Dict, Any, List, Optional
import json
import shutil

# FastMCPのインポート
from mcp.server.fastmcp import FastMCP

# PlanningManagerAgentを作成する関数をインポート
from planning_agents.planning_manager import create_planning_manager_agent

# ロガーの設定
logger = logging.getLogger(__name__)

# ファイル管理ユーティリティのインポート
from utils.file_manager import FileManager

# reset_plan で使用するため FileManager のインスタンスを作成
file_manager = FileManager()

# FastMCPサーバーインスタンスの作成
mcp_server = FastMCP("planning_agent")

@mcp_server.tool()
def create_plan(task_description: str) -> str:
    """
    ユーザーからのタスク説明に基づき、全く新しい計画を作成します。
    このツールは、プロジェクトの初期段階や、既存の計画を完全に破棄して新しい計画を立てる場合に使用します。
    呼び出すと、まず既存のプロジェクトデータ（プラン、要件、課題）がアーカイブされ、その後、タスク分析、要件定義、計画作成が行われます。

    Args:
        task_description (str): 実行したいタスク内容の説明。

    Returns:
        str: 作成された計画（通常はYAML形式の文字列）。情報が不足する場合でも、現時点での最善の計画を返します。
    """
    logger.info(f"create_planが呼び出されました: task_description='{task_description[:50]}...'")
    try:
        # 既存プロジェクトデータ（プラン、要件、課題）をアーカイブ
        try:
            archived_files = file_manager.archive_existing_project_data()
            if archived_files:
                logger.info(f"既存のプロジェクト関連ファイル {len(archived_files)} 件をアーカイブしました。")
        except Exception as archive_e:
            logger.warning(f"既存プロジェクトデータのアーカイブ中にエラーが発生しました: {archive_e}", exc_info=True)
            # アーカイブエラーは処理を続行するが、警告を出す

        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""**ユーザーから受け取った以下のタスク説明を達成するための計画を作成してください。**
タスク説明そのものを計画するのではなく、タスク説明に書かれた目標を達成するためのステップバイステップの計画が必要です。

タスク説明:
{task_description}

**指示:**
1.  タスク説明を分析し、それを達成するために必要な具体的な要件を抽出し、整理してください。
2.  抽出した要件を `save_requirements` ツールで保存してください。
3.  定義した要件に基づいて、タスク達成のための具体的なサブタスクに分解された実行計画（プラン）を作成してください。
    **重要:** 各サブタスクには、明確な入力（inputs）と出力（outputs）を定義してください。これにより、タスク間の連携がスムーズになり、実行の確実性が高まります。
4.  作成したプランを `save_plan` ツールで保存してください。
5.  **最終的な応答** としては、作成したプランの内容に加えて、**プランに含まれる最初のサブタスク（通常は `order: 1`）を実行するための具体的な指示** を含めて返してください。
    指示には、**そのサブタスクの入力（inputs）を受け取り、どのように処理して出力（outputs）を生成するか** の概要を含めてください。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for create_plan: {result_text}")
        # 次のアクションを促す定型文を追加
        guidance = "\\n\\n---\\n**次のステップ:** サブタスク完了後は `update_plan` で完了報告をしてください。サブタスク実行中に問題が発生した場合は、必ず `report_issue` で報告してください。"
        return result_text + guidance
    except Exception as e:
        logger.error(f"create_plan 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] プラン作成中に予期せぬエラーが発生しました: {e}"


@mcp_server.tool()
def update_plan(task_number: int, artifacts: List[str], comments: str) -> str:
    """
    完了したサブタスクの結果を受けて、既存の計画を更新します。
    計画の進捗状況を反映させたり、予期せぬ結果に基づいて後続タスクを修正したりする場合に使用します。

    Args:
        task_number (int): 完了したサブタスクの番号。
        artifacts (List[str]): サブタスク実行によって生成された成果物（ファイルパスなど）のリスト。
        comments (str): 計画の更新に考慮すべき点や、後続タスクへの影響に関するコメント。

    Returns:
        str: 更新された計画（通常はYAML形式の文字列）。情報が不足する場合でも、現時点での最善の更新計画を返します。
    """
    logger.info(f"update_planが呼び出されました: task_number={task_number}")
    try:
        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""サブタスク {task_number} が完了しました。以下の情報に基づいてプランを更新してください。
情報が不足している場合でも、**現時点で得られている情報に基づいて最善と思われるプランに更新してください。** 質問を返す必要はありません。

完了タスク情報:
-   実施済みサブタスク番号: {task_number}
-   生成された成果物: {', '.join(artifacts) if artifacts else 'なし'}
-   コメント: {comments}

**指示:**
1.  現在アクティブなプランファイルを `load_plan` ツールで読み込んでください。
2.  読み込んだプランと完了タスク情報を照らし合わせ、プランのステータス（完了、未完了など）を更新してください。
3.  成果物やコメントを考慮し、残りのタスク内容や順序を調整する必要があれば更新してください。
4.  更新したプラン全体を `save_plan` ツールで保存してください。
5.  必要に応じて、関連する要件（`load_requirements`）や課題（`load_issues`）も参照して、プラン更新の判断材料としてください。
6.  **最終的な応答** としては、更新されたプランの内容に加えて、**次に実行すべき未完了のサブタスク（最も小さい `order` を持つ `status: pending` のタスク）を実行するための具体的な指示** を含めて返してください。
    指示には、**そのサブタスクの入力（inputs）を受け取り、どのように処理して出力（outputs）を生成するか** の概要を含めてください。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for update_plan: {result_text}")
        # 次のアクションを促す定型文を追加
        guidance = "\\n\\n---\\n**次のステップ:** サブタスク完了後は `update_plan` で完了報告をしてください。サブタスク実行中に問題が発生した場合は、必ず `report_issue` で報告してください。"
        return result_text + guidance
    except Exception as e:
        logger.error(f"update_plan 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] プラン更新中に予期せぬエラーが発生しました: {e}"


@mcp_server.tool()
def report_issue(task_number: int, issue_description: str) -> str:
    """
    サブタスク実行中に発生した問題やブロッカーを報告し、対応方針の策定を依頼します。
    計画通りに進まなくなった場合や、予期せぬ障害が発生した場合に使用します。

    Args:
        task_number (int): 問題が発生したサブタスクの番号。
        issue_description (str): 発生した問題の詳細な説明。

    Returns:
        str: 問題への対応方針（計画修正案を含む場合がある）。情報が不足する場合でも、現時点での最善の対応方針を返します。
    """
    logger.info(f"report_issueが呼び出されました: task_number={task_number}, description='{issue_description[:50]}...'" )
    try:
        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""サブタスク {task_number} の実行中に以下の課題が発生しました。
プラン全体を確認し、具体的な対応方針を示してください。
情報が不足している場合でも、**現時点で得られている情報に基づいて最善と思われる対応方針を提案してください。** 質問を返す必要はありません。

発生した課題:
-   課題発生タスク番号: {task_number}
-   課題内容: {issue_description}

**指示:**
1.  まず、発生した課題を `save_issue` ツールで保存してください。
2.  対応方針を検討するために、`load_plan` ツールで現在のプランを読み込んでください。必要であれば `load_requirements` ツールで関連する要件も読み込んでください。
3.  課題の内容と現在のプラン・要件を分析し、以下のいずれかを行ってください。
    a.  **対応方針の決定:** 課題解決のための具体的なアクション（プランの修正、追加タスクの定義など）を決定してください。もしプランを修正する場合は、`save_plan` ツールで更新内容を保存してください。
4.  最終的な応答としては、決定した対応方針（プラン修正が必要な場合はその概要を含む）のみを返してください。ツール呼び出しの結果ではなく、方針を直接返します。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for report_issue: {result_text}")
        return result_text
    except Exception as e:
        logger.error(f"report_issue 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] 課題報告の処理中に予期せぬエラーが発生しました: {e}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Planning Agent MCPサーバーを起動します...")
    # stdioトランスポートを使用してサーバーを起動
    # クライアント（例: Claude Desktop, IDE）はこのプロセスと標準入出力で通信します
    mcp_server.run(transport='stdio') 