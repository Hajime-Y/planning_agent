"""
Smolagentsツールのテスト

このモジュールはSmolagentsのツールとして実装された関数をテストします。
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
import yaml

from utils.tools import (
    save_yaml, load_yaml,
    save_requirements, load_requirements,
    save_plan, load_plan,
    save_issue, load_issues,
    list_plans, list_requirements,
    backup_plan, delete_plan
)
from utils.file_manager import FileManager


class TestTools:
    """Smolagentsツールのテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用の一時ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # テスト終了後にディレクトリを削除
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def setup_file_manager(self, monkeypatch):
        """FileManagerのインスタンスを一時ディレクトリを使うようにパッチする"""
        temp_dir = tempfile.mkdtemp()
        
        # ツールモジュール内の_file_managerを一時ディレクトリを使うインスタンスに置き換える
        import utils.tools
        monkeypatch.setattr(utils.tools, "_file_manager", FileManager(base_dir=temp_dir))
        
        yield temp_dir
        
        # テスト終了後にディレクトリを削除
        shutil.rmtree(temp_dir)
    
    def test_save_and_load_yaml(self, temp_dir):
        """save_yamlとload_yamlツールのテスト"""
        file_path = os.path.join(temp_dir, "test.yaml")
        data = {"name": "テストデータ", "values": [1, 2, 3]}
        
        # 保存
        result = save_yaml(file_path, data)
        assert result == file_path
        assert Path(file_path).exists()
        
        # 読み込み
        loaded_data = load_yaml(file_path)
        assert loaded_data["name"] == "テストデータ"
        assert loaded_data["values"] == [1, 2, 3]
    
    def test_save_and_load_requirements(self, setup_file_manager):
        """save_requirementsとload_requirementsツールのテスト"""
        task_id = "test-task-101"
        requirements = {
            "title": "ツールテスト",
            "description": "要件ツールのテスト"
        }
        
        # 保存
        path = save_requirements(task_id, requirements)
        assert Path(path).exists()
        
        # 読み込み
        loaded = load_requirements(task_id)
        assert loaded["title"] == "ツールテスト"
        assert loaded["description"] == "要件ツールのテスト"
        assert loaded["task_id"] == task_id
    
    def test_save_and_load_plan(self, setup_file_manager):
        """save_planとload_planツールのテスト"""
        plan_id = "test-plan-101"
        plan = {
            "description": "プランツールのテスト",
            "subtasks": [{"id": "sub1", "description": "サブタスク1"}]
        }
        
        # 保存
        result = save_plan(plan_id, plan)
        assert "プランを保存しました" in result
        assert "バージョン: 1" in result
        
        # 読み込み
        loaded = load_plan(plan_id)
        assert loaded["description"] == "プランツールのテスト"
        assert loaded["subtasks"][0]["id"] == "sub1"
        assert loaded["version"] == 1
    
    def test_save_and_load_issues(self, setup_file_manager):
        """save_issueとload_issuesツールのテスト"""
        task_id = "test-task-102"
        issue = {
            "description": "課題ツールのテスト",
            "status": "open"
        }
        
        # 保存
        path = save_issue(task_id, issue)
        assert Path(path).exists()
        
        # 読み込み
        loaded = load_issues(task_id)
        assert loaded["task_id"] == task_id
        assert len(loaded["issues"]) == 1
        assert loaded["issues"][0]["description"] == "課題ツールのテスト"
    
    def test_list_plans_and_requirements(self, setup_file_manager):
        """list_plansとlist_requirementsツールのテスト"""
        # 要件とプランを作成
        save_requirements("task-list-1", {"description": "リストテスト1"})
        save_requirements("task-list-2", {"description": "リストテスト2"})
        
        save_plan("plan-list-1", {"description": "プランリストテスト1"})
        save_plan("plan-list-2", {"description": "プランリストテスト2"})
        
        # リスト取得
        tasks = list_requirements()
        plans = list_plans()
        
        assert "task-list-1" in tasks
        assert "task-list-2" in tasks
        assert "plan-list-1" in plans
        assert "plan-list-2" in plans
    
    def test_backup_and_delete_plan(self, setup_file_manager):
        """backup_planとdelete_planツールのテスト"""
        plan_id = "test-plan-backup"
        
        # プランを保存
        save_plan(plan_id, {"description": "バックアップテスト"})
        
        # バックアップを作成
        backup_path = backup_plan(plan_id)
        assert backup_path is not None
        assert Path(backup_path).exists()
        
        # プランを削除
        result = delete_plan(plan_id)
        assert result is True
        
        # プランが削除されていることを確認
        with pytest.raises(FileNotFoundError):
            load_plan(plan_id) 