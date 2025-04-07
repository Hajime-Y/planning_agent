"""
mcp_interface/server.py のユニットテスト
"""

import pytest
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import patch, MagicMock
from pathlib import Path # Path オブジェクトを使うため
import tempfile # 一時ディレクトリ作成用
import shutil # ディレクトリ削除用

# テスト対象の関数をインポート
from mcp_interface.server import create_plan, update_plan, report_issue, reset_plan, mcp_server
# FileManager もインポート (Mock作成のため)
from utils.file_manager import FileManager, RequirementsData, PlanData, IssueFileData, Subtask, Issue

# --- モック設定 --- 

# 実際のAgent呼び出しをモック化する (LLMコールを防ぐ)
@pytest.fixture(autouse=True)
def mock_agent_run(monkeypatch):
    mock_agent = MagicMock()
    # run メソッドが常に固定の文字列を返すように設定
    mock_agent.run.return_value = "Mock agent response"
    # create_planning_manager_agent がこのモックエージェントを返すようにパッチ
    monkeypatch.setattr("mcp_interface.server.create_planning_manager_agent", lambda: mock_agent)
    return mock_agent

# FileManager をモック化し、一時ディレクトリを使う
@pytest.fixture
def setup_mock_file_manager(monkeypatch, tmp_path):
    """一時ディレクトリを使うMock FileManagerを作成し、パッチする"""
    # tmp_path は pytest が提供する一時ディレクトリ用の fixture
    mock_fm = FileManager(base_dir=str(tmp_path)) # 一時ディレクトリで初期化

    # サーバーモジュール内の file_manager を差し替え
    monkeypatch.setattr("mcp_interface.server.file_manager", mock_fm)

    # delete_plan もモック化しておく (実際のファイル削除を防ぐため)
    # 必要なら他のメソッドもモック化する
    monkeypatch.setattr(mock_fm, "delete_plan", MagicMock(return_value=True))

    yield mock_fm, tmp_path # FileManagerのモックと一時ディレクトリのパスを返す

# --- テストケース --- 

def test_create_plan(mock_agent_run):
    """create_plan 関数の基本的なテスト (Agent呼び出し確認)"""
    task_desc = "テストタスクの説明"
    result = create_plan(task_description=task_desc)
    # Agent の run が呼ばれたか、内容はモックの戻り値かを確認
    mock_agent_run.run.assert_called_once()
    assert result == "Mock agent response"

def test_update_plan(mock_agent_run):
    """update_plan 関数の基本的なテスト (Agent呼び出し確認)"""
    result = update_plan(task_number=1, artifacts=["/path/to/artifact"], comments="コメント")
    mock_agent_run.run.assert_called_once()
    assert result == "Mock agent response"

def test_report_issue(mock_agent_run):
    """report_issue 関数の基本的なテスト (Agent呼び出し確認)"""
    result = report_issue(task_number=2, issue_description="問題発生")
    mock_agent_run.run.assert_called_once()
    assert result == "Mock agent response"

def test_reset_plan(setup_mock_file_manager):
    """reset_plan 関数のテスト (ファイル削除の確認)"""
    mock_fm, temp_dir = setup_mock_file_manager

    # テスト用のファイルを作成
    plan_id = "plan-to-reset"
    task_id = "task-to-reset"
    req_file = mock_fm.requirements_dir / f"{task_id}.yaml"
    plan_file = mock_fm.plans_dir / f"{plan_id}.yaml"
    issue_file = mock_fm.issues_dir / f"{task_id}.yaml"
    history_dir = mock_fm.history_dir / plan_id
    history_file = history_dir / "v1_test.yaml"

    req_file.touch()
    plan_file.touch()
    issue_file.touch()
    history_dir.mkdir()
    history_file.touch()

    # reset_plan を実行
    result = reset_plan()

    # ステータスとメッセージを確認
    assert result["status"] == "success"
    assert "リセットが完了しました" in result["message"]

    # delete_plan が呼ばれたか確認 (Mockのおかげ)
    mock_fm.delete_plan.assert_called_once_with(plan_id)

    # 要件ファイルと課題ファイルが削除されたか確認 (直接確認)
    assert not req_file.exists()
    assert not issue_file.exists()
    # plan_file と history_dir は delete_plan が削除するはず (モックされている)
