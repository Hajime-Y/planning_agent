"""
FileManagerクラスのテスト

このモジュールはFileManagerクラスの機能を網羅的にテストします。
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
import yaml

from utils.file_manager import FileManager, save_yaml_file, load_yaml_file


class TestFileManager:
    """FileManagerクラスのテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用の一時ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # テスト終了後にディレクトリを削除
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def file_manager(self, temp_dir):
        """テスト用のFileManagerインスタンスを作成"""
        return FileManager(base_dir=temp_dir)
    
    def test_init_creates_directories(self, temp_dir):
        """初期化時に必要なディレクトリが作成されることを確認"""
        fm = FileManager(base_dir=temp_dir)
        
        # 各ディレクトリが存在するか確認
        assert Path(temp_dir).exists()
        assert (Path(temp_dir) / "requirements").exists()
        assert (Path(temp_dir) / "plans").exists()
        assert (Path(temp_dir) / "issues").exists()
        assert (Path(temp_dir) / "history").exists()
    
    def test_save_requirements(self, file_manager):
        """要件ファイルの保存機能をテスト"""
        task_id = "test-task-001"
        requirements = {
            "title": "テスト要件",
            "description": "これはテストです",
            "constraints": ["制約1", "制約2"]
        }
        
        file_path = file_manager.save_requirements(task_id, requirements)
        
        # ファイルが作成されたことを確認
        assert Path(file_path).exists()
        
        # ファイルの内容を確認
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["title"] == "テスト要件"
        assert saved_data["description"] == "これはテストです"
        assert "task_id" in saved_data
        assert "created_at" in saved_data
    
    def test_load_requirements(self, file_manager):
        """要件ファイルの読み込み機能をテスト"""
        task_id = "test-task-002"
        requirements = {
            "title": "テスト要件2",
            "description": "これは読み込みテスト用です",
        }
        
        # ファイルを保存
        file_manager.save_requirements(task_id, requirements)
        
        # ファイルを読み込み
        loaded_data = file_manager.load_requirements(task_id)
        
        assert loaded_data["title"] == "テスト要件2"
        assert loaded_data["description"] == "これは読み込みテスト用です"
        assert loaded_data["task_id"] == task_id
    
    def test_save_plan(self, file_manager):
        """プランファイルの保存機能をテスト"""
        plan_id = "test-plan-001"
        task_id = "test-task-003"
        plan = {
            "task_id": task_id,
            "status": "in_progress",
            "subtasks": [
                {"id": "subtask-001", "description": "サブタスク1", "status": "pending"},
                {"id": "subtask-002", "description": "サブタスク2", "status": "pending"}
            ]
        }
        
        file_path, version = file_manager.save_plan(plan_id, plan)
        
        # ファイルが作成されたことを確認
        assert Path(file_path).exists()
        
        # バージョンと内容を確認
        assert version == 1
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["task_id"] == task_id
        assert saved_data["version"] == 1
        assert "created_at" in saved_data
        assert "updated_at" in saved_data
    
    def test_plan_versioning(self, file_manager):
        """プランのバージョン管理機能をテスト"""
        plan_id = "test-plan-002"
        
        # 初期バージョンを保存
        plan_v1 = {"description": "初期バージョン"}
        file_path_v1, version_v1 = file_manager.save_plan(plan_id, plan_v1)
        
        # 2つ目のバージョンを保存
        plan_v2 = {"description": "2つ目のバージョン"}
        file_path_v2, version_v2 = file_manager.save_plan(plan_id, plan_v2)
        
        # バージョンが上がっていることを確認
        assert version_v1 == 1
        assert version_v2 == 2
        
        # 履歴が作成されていることを確認
        versions = file_manager.list_plan_versions(plan_id)
        assert len(versions) == 2
        
        # 最新バージョンが先に来ることを確認
        assert versions[0][0] == 2
        assert versions[1][0] == 1
    
    def test_backup_plan(self, file_manager):
        """プランのバックアップ作成機能をテスト"""
        plan_id = "test-plan-003"
        plan = {"description": "バックアップテスト"}
        
        # プランを保存
        file_manager.save_plan(plan_id, plan)
        
        # バックアップを作成
        backup_path = file_manager.backup_plan(plan_id)
        
        # バックアップファイルが存在することを確認
        assert backup_path is not None
        assert Path(backup_path).exists()
        
        # バックアップの内容が正しいことを確認
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = yaml.safe_load(f)
        
        assert backup_data["description"] == "バックアップテスト"
    
    def test_save_issue(self, file_manager):
        """課題ファイルの保存機能をテスト"""
        task_id = "test-task-004"
        issue = {
            "description": "テスト課題",
            "status": "open",
            "impact": "高"
        }
        
        file_path = file_manager.save_issue(task_id, issue)
        
        # ファイルが作成されたことを確認
        assert Path(file_path).exists()
        
        # 内容を確認
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["task_id"] == task_id
        assert "updated_at" in saved_data
        assert len(saved_data["issues"]) == 1
        assert saved_data["issues"][0]["description"] == "テスト課題"
        assert "issue_id" in saved_data["issues"][0]
    
    def test_update_issue(self, file_manager):
        """課題の更新機能をテスト"""
        task_id = "test-task-005"
        
        # 初期の課題を保存
        issue1 = {"description": "課題1"}
        file_manager.save_issue(task_id, issue1)
        
        # 課題データを読み込む
        issues_data = file_manager.load_issues(task_id)
        issue_id = issues_data["issues"][0]["issue_id"]
        
        # 課題を更新
        updated_issue = {
            "issue_id": issue_id,
            "description": "更新された課題1",
            "status": "in_progress"
        }
        file_manager.save_issue(task_id, updated_issue)
        
        # 更新された課題を確認
        issues_data = file_manager.load_issues(task_id)
        assert len(issues_data["issues"]) == 1
        assert issues_data["issues"][0]["description"] == "更新された課題1"
        assert issues_data["issues"][0]["status"] == "in_progress"
    
    def test_add_multiple_issues(self, file_manager):
        """複数の課題を追加する機能をテスト"""
        task_id = "test-task-006"
        
        # 1つ目の課題を追加
        issue1 = {"description": "課題1"}
        file_manager.save_issue(task_id, issue1)
        
        # 2つ目の課題を追加
        issue2 = {"description": "課題2"}
        file_manager.save_issue(task_id, issue2)
        
        # 課題データを確認
        issues_data = file_manager.load_issues(task_id)
        assert len(issues_data["issues"]) == 2
        descriptions = [issue["description"] for issue in issues_data["issues"]]
        assert "課題1" in descriptions
        assert "課題2" in descriptions
    
    def test_list_plans(self, file_manager):
        """プランのリスト機能をテスト"""
        # 複数のプランを作成
        file_manager.save_plan("plan1", {"description": "プラン1"})
        file_manager.save_plan("plan2", {"description": "プラン2"})
        file_manager.save_plan("plan3", {"description": "プラン3"})
        
        # プランリストを取得
        plans = file_manager.list_plans()
        
        # 作成したプランがリストに含まれているか確認
        assert "plan1" in plans
        assert "plan2" in plans
        assert "plan3" in plans
    
    def test_list_requirements(self, file_manager):
        """タスクのリスト機能をテスト"""
        # 複数の要件を作成
        file_manager.save_requirements("task1", {"description": "タスク1"})
        file_manager.save_requirements("task2", {"description": "タスク2"})
        
        # タスクリストを取得
        tasks = file_manager.list_requirements()
        
        # 作成したタスクがリストに含まれているか確認
        assert "task1" in tasks
        assert "task2" in tasks
    
    def test_delete_plan(self, file_manager):
        """プラン削除機能をテスト"""
        plan_id = "test-plan-004"
        
        # 初期バージョンを保存
        file_manager.save_plan(plan_id, {"description": "削除テスト"})
        
        # 2つ目のバージョンを保存（履歴を作成）
        file_manager.save_plan(plan_id, {"description": "削除テスト更新"})
        
        # プランが存在することを確認
        assert Path(file_manager.plans_dir / f"{plan_id}.yaml").exists()
        
        # プランを削除
        result = file_manager.delete_plan(plan_id)
        
        # 削除が成功したことを確認
        assert result is True
        
        # ファイルが削除されたことを確認
        assert not Path(file_manager.plans_dir / f"{plan_id}.yaml").exists()
        assert not (file_manager.history_dir / plan_id).exists()
    
    def test_save_yaml_file_utility(self, temp_dir):
        """save_yaml_file ユーティリティ関数のテスト"""
        file_path = os.path.join(temp_dir, "test", "util.yaml")
        data = {"key": "value", "list": [1, 2, 3]}
        
        # ファイルを保存
        saved_path = save_yaml_file(file_path, data)
        
        # ファイルが作成されたことを確認
        assert Path(saved_path).exists()
        
        # 内容を確認
        with open(saved_path, 'r', encoding='utf-8') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data["key"] == "value"
        assert saved_data["list"] == [1, 2, 3]
    
    def test_load_yaml_file_utility(self, temp_dir):
        """load_yaml_file ユーティリティ関数のテスト"""
        file_path = os.path.join(temp_dir, "util_load.yaml")
        data = {"test": "データ", "number": 42}
        
        # ファイルを作成
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        
        # ファイルを読み込み
        loaded_data = load_yaml_file(file_path)
        
        # 内容を確認
        assert loaded_data["test"] == "データ"
        assert loaded_data["number"] == 42
    
    def test_load_yaml_file_not_found(self, temp_dir):
        """存在しないファイルを読み込もうとした時の挙動をテスト"""
        file_path = os.path.join(temp_dir, "not_exists.yaml")
        
        # 存在しないファイルを読み込もうとするとFileNotFoundErrorが発生することを確認
        with pytest.raises(FileNotFoundError):
            load_yaml_file(file_path) 