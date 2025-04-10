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
from mcp_interface.server import create_plan, update_plan, report_issue, mcp_server
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

def test_create_plan(mock_agent_run, setup_mock_file_manager):
    """create_plan 関数のテスト (Agent呼び出しと既存プランアーカイブ確認)"""
    mock_fm, temp_dir = setup_mock_file_manager

    # テスト用の既存プランファイルを作成
    existing_plan_id = "existing-plan"
    existing_plan_file = mock_fm.plans_dir / f"{existing_plan_id}.yaml"
    existing_plan_file.touch()
    assert existing_plan_file.exists() # 事前確認

    task_desc = "テストタスクの説明"
    result = create_plan(task_description=task_desc)
    
    # Agent の run が呼ばれたか、内容はモックの戻り値かを確認
    mock_agent_run.run.assert_called_once()
    assert result == "Mock agent response"

    # 既存プランがアーカイブされたか（元の場所にない）を確認
    assert not existing_plan_file.exists()
    # アーカイブ先のディレクトリとファイルが存在するか確認
    # archive_existing_plans がタイムスタンプを使うため、正確なディレクトリ名は取得難しい
    # history ディレクトリ内に archive_* というディレクトリが1つできているかで確認
    archive_dirs = list(mock_fm.history_dir.glob("archive_*"))
    assert len(archive_dirs) == 1
    # そのディレクトリ内に移動されたファイルがあるか確認
    archived_file = archive_dirs[0] / f"{existing_plan_id}.yaml"
    assert archived_file.exists()

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
