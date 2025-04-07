"""
mcp_interface/server.py のユニットテスト
"""

import pytest
from typing import Dict, Any

# テスト対象の関数をインポート
from mcp_interface.server import create_plan, update_plan, report_issue, reset_plan

# モック用のFileManager (実際のファイル操作を防ぐ)
class MockFileManager:
    def save_requirements(self, task_id: str, requirements: Dict[str, Any]) -> str:
        return f"mock_requirements/{task_id}.yaml"

    def save_plan(self, plan_id: str, plan: Dict[str, Any]) -> tuple[str, int]:
        return f"mock_plans/{plan_id}.yaml", 1

    def load_plan(self, plan_id: str) -> Dict[str, Any]:
        if plan_id == "existing_plan":
            return {"plan_id": plan_id, "task_id": "task-123", "version": 1, "subtasks": []}
        raise FileNotFoundError(f"プランが見つかりません: {plan_id}")

    def backup_plan(self, plan_id: str) -> str:
        return f"mock_history/{plan_id}/v1_backup.yaml"

    def save_issue(self, task_id: str, issue: Dict[str, Any]) -> str:
        return f"mock_issues/{task_id}.yaml"
    
    def delete_plan(self, plan_id: str) -> bool:
        return True

# テスト内でFileManagerをモックに置き換える
@pytest.fixture(autouse=True)
def mock_file_manager(monkeypatch):
    mock_instance = MockFileManager()
    # mcp_interface.server モジュール内の file_manager をモックに差し替える
    monkeypatch.setattr("mcp_interface.server.file_manager", mock_instance)

def test_create_plan():
    """create_plan 関数の基本的なテスト"""
    result = create_plan(task_description="テストタスクの説明")
    assert isinstance(result, dict)
    assert "status" in result
    assert "plan_id" in result
    assert "task_id" in result
    assert result["status"] == "pending" # ダミー実装の確認

def test_update_plan():
    """update_plan 関数の基本的なテスト"""
    result = update_plan(plan_id="existing_plan", updates={"status": "in_progress"})
    assert isinstance(result, dict)
    assert "status" in result
    assert "plan_id" in result
    assert result["status"] == "pending" # ダミー実装の確認

def test_report_issue():
    """report_issue 関数の基本的なテスト"""
    result = report_issue(plan_id="existing_plan", description="問題が発生しました")
    assert isinstance(result, dict)
    assert "status" in result
    assert "plan_id" in result
    assert "suggested_next_steps" in result
    assert result["status"] == "pending" # ダミー実装の確認

def test_reset_plan_with_backup():
    """reset_plan 関数の基本的なテスト (バックアップあり)"""
    result = reset_plan(plan_id="existing_plan", backup=True)
    assert isinstance(result, dict)
    assert "status" in result
    assert "plan_id" in result
    assert "backup_path" in result
    assert result["status"] == "success" # ダミー実装の確認
    assert result["backup_path"] is not None

def test_reset_plan_without_backup():
    """reset_plan 関数の基本的なテスト (バックアップなし)"""
    result = reset_plan(plan_id="existing_plan", backup=False)
    assert isinstance(result, dict)
    assert "status" in result
    assert "plan_id" in result
    assert "backup_path" in result
    assert result["status"] == "success" # ダミー実装の確認
    assert result["backup_path"] is None
