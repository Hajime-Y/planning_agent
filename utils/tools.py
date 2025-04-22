"""
Smolagentsツール集

このモジュールはSmolagentsのCodeAgentで使用できるツールを提供します。
各ツールは@toolデコレータでラップされています。
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys
import os

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

# グローバルなシングルトンインスタンス変数
_file_manager_instance: Optional[FileManager] = None

def init_file_manager(base_dir: str) -> None:
    """FileManagerのシングルトンインスタンスを初期化します。"""
    global _file_manager_instance
    if _file_manager_instance is not None:
        # 必要に応じて警告を出すか、エラーにするか、あるいは何もしないか
        # ここでは、既存のインスタンスがある場合は何もしない（再初期化を許可しない）
        print(f"WARN: FileManager is already initialized with base_dir: {_file_manager_instance.base_dir}", file=sys.stderr)
        return
    _file_manager_instance = FileManager(base_dir=base_dir)

def get_file_manager() -> FileManager:
    """初期化済みのFileManagerシングルトンインスタンスを取得します。"""
    if _file_manager_instance is None:
        raise RuntimeError("FileManager has not been initialized. Call init_file_manager() first.")
    return _file_manager_instance


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
    fm = get_file_manager()
    # created_at は FileManager 側で処理されるので渡さない
    return fm.save_requirements(
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
    fm = get_file_manager()
    return fm.load_requirements(task_id)


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
        subtasks: サブタスクのリスト。各サブタスクは Subtask 型の辞書で、'id', 'description', 'status', 'order', 'inputs', 'outputs' をキーとして持ちます。
                  例 (Pythonスクリプト作成タスクの場合): [
                      {
                          'id': 's1', 'description': '要件分析と定義書の作成',
                          'status': 'completed', 'order': 1,
                          'inputs': ['task_id'], 'outputs': ['data/requirements/task_id.yaml']
                      },
                      {
                          'id': 's2', 'description': 'スクリプト設計と設計書の作成',
                          'status': 'in_progress', 'order': 2,
                          'inputs': ['data/requirements/task_id.yaml'], 'outputs': ['docs/design/task_id_design.md']
                      },
                      {
                          'id': 's3', 'description': 'Pythonスクリプトの実装',
                          'status': 'pending', 'order': 3,
                          'inputs': ['docs/design/task_id_design.md'], 'outputs': ['src/my_script.py']
                      },
                      {
                          'id': 's4', 'description': '単体テストコードの作成',
                          'status': 'pending', 'order': 4,
                          'inputs': ['src/my_script.py'], 'outputs': ['tests/test_my_script.py']
                      },
                      {
                          'id': 's5', 'description': '単体テストの実行と結果レポート生成',
                          'status': 'pending', 'order': 5,
                          'inputs': ['src/my_script.py', 'tests/test_my_script.py'], 'outputs': ['reports/test_results.xml']
                      }
                  ]

    Returns:
        保存/更新結果を示すメッセージ (例: "プランを保存しました: path/to/plan.yaml (バージョン: 2)")
    """
    fm = get_file_manager()
    # created_at や version は FileManager 側で処理
    file_path, version = fm.save_plan(
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
    fm = get_file_manager()
    return fm.load_plan(plan_id)


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
    fm = get_file_manager()
    # created_at は FileManager 側で処理
    file_path, saved_issue_id = fm.save_issue(
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
    fm = get_file_manager()
    return fm.load_issues(task_id)

# list_plans, list_requirements, delete_plan は不要なので削除 