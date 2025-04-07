"""
Smolagentsツール集

このモジュールはSmolagentsのCodeAgentで使用できるツールを提供します。
各ツールは@toolデコレータでラップされています。
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# テスト時の互換性問題を回避するためのフォールバック
try:
    from smolagents import tool
except ImportError:
    # モックツールデコレータ（テスト用）
    def tool(func):
        """テスト用のモックツールデコレータ"""
        return func

# file_manager から必要なクラスと型定義をインポート
from .file_manager import (
    FileManager,
    RequirementsData,
    PlanData,
    IssueFileData,
    Subtask,       # save_plan で使う
)


# ファイルマネージャのインスタンス
# データディレクトリの場所はここで一元管理
_file_manager = FileManager(base_dir="./data")


@tool
def save_requirements(
    task_id: str,
    title: str,
    description: str,
    constraints: List[str],
    resources: List[str],
) -> str:
    """タスクの要件データをYAMLファイルに保存します。
    既存のファイルがある場合は更新します。

    Args:
        task_id: タスクID
        title: タスクのタイトル
        description: タスクの説明
        constraints: 制約条件の文字列リスト
        resources: 利用可能なリソースの文字列リスト

    Returns:
        保存したファイルのパス
    """
    # created_at は FileManager 側で処理されるので渡さない
    return _file_manager.save_requirements(
        task_id=task_id,
        title=title,
        description=description,
        constraints=constraints,
        resources=resources,
    )


@tool
def load_requirements(task_id: str) -> RequirementsData:
    """タスクの要件データをYAMLファイルから読み込みます。

    Args:
        task_id: タスクID

    Returns:
        読み込んだ要件データ (RequirementsData 型)
    """
    return _file_manager.load_requirements(task_id)


@tool
def save_plan(
    plan_id: str,
    task_id: str,
    status: str,
    subtasks: List[Subtask],
) -> str:
    """プランデータをYAMLファイルに保存します。
    既存のファイルがある場合は更新し、自動でバージョン管理とバックアップを行います。

    Args:
        plan_id: プランID
        task_id: 関連するタスクID
        status: プランのステータス (例: 'in_progress', 'completed')
        subtasks: サブタスクのリスト (例: [{'id': 's1', 'description': 'd', 'status': 'pending', 'order': 1, 'inputs': [], 'outputs': []}])

    Returns:
        保存/更新結果を示すメッセージ (例: "プランを保存しました: path/to/plan.yaml (バージョン: 2)")
    """
    # created_at や version は FileManager 側で処理
    file_path, version = _file_manager.save_plan(
        plan_id=plan_id,
        task_id=task_id,
        status=status,
        subtasks=subtasks,
    )
    return f"プランを保存しました: {file_path} (バージョン: {version})"


@tool
def load_plan(plan_id: str) -> PlanData:
    """プランデータをYAMLファイルから読み込みます。

    Args:
        plan_id: プランID

    Returns:
        読み込んだプランデータ (PlanData 型)
    """
    return _file_manager.load_plan(plan_id)


@tool
def save_issue(
    task_id: str,
    issue_id: Optional[str], # Noneの場合は新規作成
    status: str,
    description: str,
    impact: str,
    solution: str,
    remarks: Optional[str],
    related_subtasks: List[str],
) -> str:
    """個別の課題を課題ファイルに追加または更新します。

    Args:
        task_id: 関連するタスクID
        issue_id: 更新する課題ID (新規作成の場合はNone)
        status: 課題のステータス (例: 'open', 'closed')
        description: 課題の説明
        impact: 課題の影響
        solution: 解決策
        remarks: 備考 (任意)
        related_subtasks: 関連するサブタスクIDのリスト

    Returns:
        保存/更新結果を示すメッセージ (例: "課題 'issue-task-001-001' を保存しました: path/to/issues.yaml")
    """
    # created_at は FileManager 側で処理
    file_path, saved_issue_id = _file_manager.save_issue(
        task_id=task_id,
        issue_id=issue_id,
        status=status,
        description=description,
        impact=impact,
        solution=solution,
        remarks=remarks,
        related_subtasks=related_subtasks,
    )
    if saved_issue_id == "NotSaved":
         return f"課題の保存に失敗しました (task_id: {task_id}, issue_id: {issue_id})"
    elif saved_issue_id == "Error":
         return f"課題の保存中にエラーが発生しました (task_id: {task_id}, issue_id: {issue_id})"
    else:
        action = "更新" if issue_id else "保存"
        return f"課題 '{saved_issue_id}' を{action}しました: {file_path}"


@tool
def load_issues(task_id: str) -> IssueFileData:
    """課題データをYAMLファイルから読み込みます。

    Args:
        task_id: タスクID

    Returns:
        読み込んだ課題データ (IssueFileData 型)
    """
    return _file_manager.load_issues(task_id)

# list_plans, list_requirements, delete_plan は不要なので削除 