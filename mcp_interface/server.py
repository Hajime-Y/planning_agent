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
    新しいタスクからプランを作成、または要件定義のための質問を返します。
    作成された要件とプランは、適切なツール（save_requirements, save_plan）で保存する必要があります。

    Args:
        task_description: タスクの説明

    Returns:
        作成されたプラン、または要件定義のための質問事項（テキスト形式）
    """
    logger.info(f"create_planが呼び出されました: task_description='{task_description[:50]}...'" )
    try:
        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""以下のタスクの説明に基づいて、要件を定義し、プランを作成してください。
もし情報が不足している場合は、要件定義のための質問をしてください。

タスク説明:
{task_description}

**指示:**
1.  タスク説明から具体的な要件を抽出し、整理してください。
2.  抽出した要件を `save_requirements` ツールで保存してください。
3.  定義した要件に基づいて、具体的なサブタスクに分解された実行計画（プラン）を作成してください。
4.  作成したプランを `save_plan` ツールで保存してください。
5.  最終的な応答としては、作成したプランの内容、または要件定義のための質問のみを返してください。ツール呼び出しの結果ではなく、プラン自体や質問を直接返します。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for create_plan: {result_text}")
        return result_text
    except Exception as e:
        logger.error(f"create_plan 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] プラン作成中に予期せぬエラーが発生しました: {e}"


@mcp_server.tool()
def update_plan(task_number: int, artifacts: List[str], comments: str) -> str:
    """
    実施済みタスクの結果に基づきプランを更新、またはプラン更新のための質問を返します。
    プランの読み込み、更新、保存には適切なツール（load_plan, save_plan）を使用する必要があります。

    Args:
        task_number: 実施したサブタスクの番号
        artifacts: 生成された成果物のリスト（ファイルパスなど）
        comments: 今後のタスクに影響を及ぼしそうな内容に関するコメント

    Returns:
        更新されたプラン、またはプラン更新のための質問事項（テキスト形式）
    """
    logger.info(f"update_planが呼び出されました: task_number={task_number}")
    try:
        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""サブタスク {task_number} が完了しました。以下の情報に基づいてプランを更新するか、プラン更新のための質問をしてください。

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
6.  最終的な応答としては、更新されたプランの内容、またはプラン更新のための質問のみを返してください。ツール呼び出しの結果ではなく、更新後のプラン自体や質問を直接返します。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for update_plan: {result_text}")
        return result_text
    except Exception as e:
        logger.error(f"update_plan 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] プラン更新中に予期せぬエラーが発生しました: {e}"


@mcp_server.tool()
def report_issue(task_number: int, issue_description: str) -> str:
    """
    実行中のタスクで発生した課題を報告し、対応方針または追加質問を返します。
    課題の保存、プランや要件の読み込みには適切なツール（save_issue, load_plan, load_requirements）を使用する必要があります。

    Args:
        task_number: 問題が発生したサブタスクの番号
        issue_description: 課題の内容

    Returns:
        プラン全体を確認しての課題対応方針、または課題分析のための追加質問事項（テキスト形式）
    """
    logger.info(f"report_issueが呼び出されました: task_number={task_number}, description='{issue_description[:50]}...'" )
    try:
        agent = create_planning_manager_agent()
        # プロンプトにツール利用の指示を追加
        prompt = f"""サブタスク {task_number} の実行中に以下の課題が発生しました。
プラン全体を確認し、対応方針を示すか、分析のために追加の質問をしてください。

発生した課題:
-   課題発生タスク番号: {task_number}
-   課題内容: {issue_description}

**指示:**
1.  まず、発生した課題を `save_issue` ツールで保存してください。
2.  対応方針を検討するために、`load_plan` ツールで現在のプランを読み込んでください。必要であれば `load_requirements` ツールで関連する要件も読み込んでください。
3.  課題の内容と現在のプラン・要件を分析し、以下のいずれかを行ってください。
    a.  **対応方針の決定:** 課題解決のための具体的なアクション（プランの修正、追加タスクの定義など）を決定してください。もしプランを修正する場合は、`save_plan` ツールで更新内容を保存してください。
    b.  **追加質問の生成:** 対応方針を決定するために情報が不足している場合は、必要な情報を得るための質問を生成してください。
4.  最終的な応答としては、決定した対応方針（プラン修正が必要な場合はその概要を含む）、または追加の質問のみを返してください。ツール呼び出しの結果ではなく、方針や質問を直接返します。
"""
        result_text = agent.run(prompt)
        logger.info(f"Agent run result for report_issue: {result_text}")
        return result_text
    except Exception as e:
        logger.error(f"report_issue 処理中にエラー: {e}", exc_info=True)
        return f"[エラー] 課題報告の処理中に予期せぬエラーが発生しました: {e}"


@mcp_server.tool()
def reset_plan() -> Dict[str, Any]:
    """
    これまでのプラン関連データ（要件、プラン、課題、履歴）を削除します。
    この操作ではエージェントは呼び出されません。

    Returns:
        処理結果を示す辞書
    """
    logger.info(f"reset_planが呼び出されました")
    deleted_files_count = 0
    errors = []

    try:
        # プランと履歴の削除
        plan_files = list(file_manager.plans_dir.glob("*.yaml"))
        plan_ids_to_delete = [f.stem for f in plan_files]
        logger.info(f"削除対象プランID: {plan_ids_to_delete}")

        # プランと履歴の削除
        for plan_id in plan_ids_to_delete:
            try:
                if file_manager.delete_plan(plan_id):
                    logger.info(f"プラン {plan_id} を削除しました (履歴含む)")
                    # delete_plan がTrueを返した場合、プランファイルと履歴ディレクトリが対象
                    # カウント方法は要検討だが、ひとまず1プラン=1カウントとする
                    deleted_files_count += 1
            except Exception as e:
                msg = f"プラン {plan_id} の削除中にエラー: {e}"
                logger.error(msg)
                errors.append(msg)

        # 要件ファイルの削除
        req_files = list(file_manager.requirements_dir.glob("*.yaml"))
        logger.info(f"削除対象の要件ファイル数: {len(req_files)}")
        for req_file in req_files:
            try:
                req_file.unlink()
                logger.info(f"要件ファイル {req_file.name} を削除しました")
                deleted_files_count += 1
            except Exception as e:
                msg = f"要件ファイル {req_file.name} の削除中にエラー: {e}"
                logger.error(msg)
                errors.append(msg)
        
        # 課題ファイルの削除
        issue_files = list(file_manager.issues_dir.glob("*.yaml"))
        logger.info(f"削除対象の課題ファイル数: {len(issue_files)}")
        for issue_file in issue_files:
            try:
                issue_file.unlink()
                logger.info(f"課題ファイル {issue_file.name} を削除しました")
                deleted_files_count += 1
            except Exception as e:
                msg = f"課題ファイル {issue_file.name} の削除中にエラー: {e}"
                logger.error(msg)
                errors.append(msg)

        if not errors:
            return {"status": "success", "message": f"プラン関連データのリセットが完了しました。削除ファイル数 (概算): {deleted_files_count}"}
        else:
            return {"status": "warning", "message": f"プラン関連データのリセット中に一部エラーが発生しました。削除ファイル数 (概算): {deleted_files_count}", "errors": errors}

    except Exception as e:
        logger.error(f"reset_plan 処理中に予期せぬエラー: {e}", exc_info=True)
        return {"status": "error", "message": f"プランリセット中に予期せぬエラーが発生しました: {e}"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Planning Agent MCPサーバーを起動します...")
    # stdioトランスポートを使用してサーバーを起動
    # クライアント（例: Claude Desktop, IDE）はこのプロセスと標準入出力で通信します
    mcp_server.run(transport='stdio') 