"""
MCPサーバー実装

このモジュールは、FastMCPライブラリを使用してPlanning AgentシステムのMCPサーバーを実装します。
クライアントからのリクエストを受け付け、適切なツール関数を呼び出します。
"""

import logging
from typing import Dict, Any, List, Optional

# FastMCPのインポート
from mcp.server.fastmcp import FastMCP

# ロガーの設定
logger = logging.getLogger(__name__)

# ファイル管理ユーティリティのインポート
from utils.file_manager import FileManager

# ファイルマネージャのインスタンス
file_manager = FileManager()


# FastMCPサーバーインスタンスの作成
mcp_server = FastMCP("planning_agent")


@mcp_server.tool()
def create_plan(task_description: str, 
                constraints: Optional[List[str]] = None, 
                task_id: Optional[str] = None,
                title: Optional[str] = None) -> Dict[str, Any]:
    """
    新しいタスクからプランを作成します。

    Args:
        task_description: タスクの説明
        constraints: タスクの制約条件リスト
        task_id: (オプション) 指定されたタスクID
        title: (オプション) タスクのタイトル

    Returns:
        プランID、初期プラン、または必要な場合は質問を含む辞書
    """
    logger.info(f"create_planが呼び出されました: task_description='{task_description[:50]}...'", )
    
    # TODO: PlanningManagerAgentを呼び出してプラン作成を依頼する
    pass 
    
    # 現時点ではダミーのレスポンスを返す
    # 将来的にはエージェントからの結果を返す
    dummy_plan_id = f"plan-{task_id or 'new'}"
    return {
        "status": "pending", 
        "message": "プラン作成を開始しました", 
        "plan_id": dummy_plan_id,
        "task_id": task_id or "generated_task_id" 
    }


@mcp_server.tool()
def update_plan(plan_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    既存のプランを更新します。

    Args:
        plan_id: 更新するプランのID
        updates: 更新内容（完了タスク、変更内容など）を含む辞書

    Returns:
        更新されたプラン情報を含む辞書
    """
    logger.info(f"update_planが呼び出されました: plan_id='{plan_id}'")
    
    # TODO: PlanningManagerAgentを呼び出してプラン更新を依頼する
    pass
    
    # 現時点ではダミーのレスポンスを返す
    return {
        "status": "pending", 
        "message": "プラン更新を開始しました", 
        "plan_id": plan_id
    }


@mcp_server.tool()
def report_issue(plan_id: str, description: str, 
                 impact: Optional[str] = None, 
                 suggested_actions: Optional[List[str]] = None,
                 related_subtasks: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    プラン実行中の問題を報告し、対応方針を取得します。

    Args:
        plan_id: 問題が発生したプランのID
        description: 問題の説明
        impact: (オプション) 問題の影響
        suggested_actions: (オプション) 推奨される対応策
        related_subtasks: (オプション) 関連するサブタスクIDのリスト

    Returns:
        問題の分析結果や推奨される対応策を含む辞書
    """
    logger.info(f"report_issueが呼び出されました: plan_id='{plan_id}', description='{description[:50]}...'", )
    
    # TODO: PlanningManagerAgentを呼び出して課題分析と対応策生成を依頼する
    pass
    
    # 現時点ではダミーのレスポンスを返す
    return {
        "status": "pending", 
        "message": "課題報告を受け付けました", 
        "plan_id": plan_id,
        "suggested_next_steps": ["課題を分析しています..."]
    }


@mcp_server.tool()
def reset_plan(plan_id: str, backup: bool = True) -> Dict[str, Any]:
    """
    タスク完了またはリセット要求により、プラン関連データをクリーンアップします。

    Args:
        plan_id: リセットするプランのID
        backup: (オプション) 削除前にプラン履歴をバックアップするかどうか (デフォルト: True)

    Returns:
        リセット処理の結果を含む辞書
    """
    logger.info(f"reset_planが呼び出されました: plan_id='{plan_id}', backup={backup}")
    
    # TODO: PlanningManagerAgentを呼び出してリセット処理を依頼する
    # (FileManagerを使ったファイル削除など)
    pass
    
    # 現時点ではダミーのレスポンスを返す
    try:
        if backup:
            # ダミーでバックアップ処理をシミュレート
            backup_path = f"/path/to/history/{plan_id}/backup.yaml"
            logger.info(f"プランをバックアップしました (ダミー): {backup_path}")
        else:
            backup_path = None
            
        # ダミーで削除処理をシミュレート
        logger.info(f"プランを削除しました (ダミー): {plan_id}")
        
        return {
            "status": "success", 
            "message": "プランのリセットが完了しました", 
            "plan_id": plan_id,
            "backup_path": backup_path
        }
    except Exception as e:
        logger.error(f"プランのリセット中にエラーが発生しました (ダミー): {e}")
        return {
            "status": "error",
            "message": f"プランのリセット中にエラーが発生しました: {e}",
            "plan_id": plan_id
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Planning Agent MCPサーバーを起動します...")
    # stdioトランスポートを使用してサーバーを起動
    # クライアント（例: Claude Desktop, IDE）はこのプロセスと標準入出力で通信します
    mcp_server.run(transport='stdio') 