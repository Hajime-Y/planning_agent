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

from utils.file_manager import (
    FileManager,
    RequirementsData, PlanData, IssueFileData, Issue, Subtask
)


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
        title = "テスト要件"
        description = "これはテストです"
        constraints = ["制約1", "制約2"]
        resources = ["リソース1"]

        # clarifications は削除された
        file_path = file_manager.save_requirements(
            task_id=task_id,
            title=title,
            description=description,
            constraints=constraints,
            resources=resources,
        )

        # ファイルが作成されたことを確認
        assert Path(file_path).exists()

        # ファイルの内容を確認
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data: RequirementsData = yaml.safe_load(f)

        assert saved_data["title"] == title
        assert saved_data["description"] == description
        assert saved_data["constraints"] == constraints
        assert saved_data["resources"] == resources
        assert "task_id" in saved_data
        assert "created_at" in saved_data
        assert "updated_at" in saved_data
        assert "clarifications" not in saved_data # clarificationsがないことを確認
    
    def test_load_requirements(self, file_manager):
        """要件ファイルの読み込み機能をテスト"""
        task_id = "test-task-002"
        title = "テスト要件2"
        description = "これは読み込みテスト用です"
        constraints = ["制約3"]
        resources = []

        # ファイルを保存
        file_manager.save_requirements(
            task_id=task_id,
            title=title,
            description=description,
            constraints=constraints,
            resources=resources,
        )

        # ファイルを読み込み
        loaded_data: RequirementsData = file_manager.load_requirements(task_id)

        assert loaded_data["title"] == title
        assert loaded_data["description"] == description
        assert loaded_data["constraints"] == constraints
        assert loaded_data["resources"] == resources
        assert loaded_data["task_id"] == task_id
    
    def test_save_plan(self, file_manager):
        """プランファイルの保存機能をテスト (新規作成)"""
        plan_id = "test-plan-001"
        task_id = "test-task-003"
        status = "in_progress"
        subtasks: List[Subtask] = [
            {"id": "subtask-001", "description": "サブタスク1", "status": "pending", "order": 1, "inputs": [], "outputs": []},
            {"id": "subtask-002", "description": "サブタスク2", "status": "pending", "order": 2, "inputs": [], "outputs": []}
        ]

        # 保存メソッドの引数に合わせて呼び出し
        file_path, version = file_manager.save_plan(
            plan_id=plan_id,
            task_id=task_id,
            status=status,
            subtasks=subtasks,
        )

        # ファイルが作成されたことを確認
        assert Path(file_path).exists()

        # バージョンと内容を確認
        assert version == 1
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data: PlanData = yaml.safe_load(f)

        assert saved_data["plan_id"] == plan_id
        assert saved_data["task_id"] == task_id
        assert saved_data["status"] == status
        assert saved_data["subtasks"] == subtasks
        assert saved_data["version"] == 1
        assert "created_at" in saved_data
        assert "updated_at" in saved_data
    
    def test_plan_versioning_and_backup(self, file_manager):
        """プランのバージョン管理とバックアップ機能をテスト"""
        plan_id = "test-plan-002"
        task_id = "test-task-004"

        # 初期バージョンを保存
        subtasks_v1: List[Subtask] = [{"id": "s1", "description": "v1", "status": "done", "order": 1, "inputs": [], "outputs": []}]
        file_path_v1, version_v1 = file_manager.save_plan(
            plan_id=plan_id, task_id=task_id, status="done", subtasks=subtasks_v1
        )

        # 2つ目のバージョンを保存
        subtasks_v2: List[Subtask] = [
            {"id": "s1", "description": "v1", "status": "done", "order": 1, "inputs": [], "outputs": []},
            {"id": "s2", "description": "v2", "status": "pending", "order": 2, "inputs": [], "outputs": []}
        ]
        file_path_v2, version_v2 = file_manager.save_plan(
            plan_id=plan_id, task_id=task_id, status="in_progress", subtasks=subtasks_v2
        )

        # バージョンが上がっていることを確認
        assert version_v1 == 1
        assert version_v2 == 2

        # 最新ファイルの内容を確認
        with open(file_path_v2, 'r', encoding='utf-8') as f:
            saved_data_v2: PlanData = yaml.safe_load(f)
        assert saved_data_v2["version"] == 2
        assert saved_data_v2["status"] == "in_progress"
        assert len(saved_data_v2["subtasks"]) == 2

        # 履歴ファイルが作成されていることを確認
        history_dir = file_manager.history_dir / plan_id
        assert history_dir.exists()
        # バックアップファイルは v{version}_{timestamp}.yaml 形式
        backup_files = list(history_dir.glob(f"v{version_v1}_*.yaml")) # v1のバックアップを探す
        assert len(backup_files) == 1
        backup_path = backup_files[0]

        # バックアップの内容を確認 (v1の内容のはず)
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data: PlanData = yaml.safe_load(f)

        assert backup_data["plan_id"] == plan_id
        assert backup_data["task_id"] == task_id
        assert backup_data["version"] == 1 # バックアップされた時点のバージョン
        assert backup_data["status"] == "done" # v1保存時のステータス
        assert len(backup_data["subtasks"]) == 1
        assert backup_data["subtasks"][0]["description"] == "v1"
    
    def test_save_issue_new(self, file_manager):
        """課題ファイルの保存機能をテスト (新規作成)"""
        task_id = "test-task-005"
        status = "open"
        description = "テスト課題"
        impact = "高"
        solution = "解決策A"
        remarks = "備考あり"
        related_subtasks = ["sub1"]

        # issue_id=None で新規作成
        file_path, saved_issue_id = file_manager.save_issue(
            task_id=task_id,
            issue_id=None,
            status=status,
            description=description,
            impact=impact,
            solution=solution,
            remarks=remarks,
            related_subtasks=related_subtasks
        )

        # ファイルが作成されたことを確認
        assert Path(file_path).exists()
        expected_issue_id = f"issue-{task_id}-001"
        assert saved_issue_id == expected_issue_id

        # 内容を確認
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data: IssueFileData = yaml.safe_load(f)

        assert saved_data["task_id"] == task_id
        assert "updated_at" in saved_data
        assert len(saved_data["issues"]) == 1
        saved_issue = saved_data["issues"][0]
        assert saved_issue["issue_id"] == expected_issue_id
        assert saved_issue["description"] == description
        assert saved_issue["status"] == status
        assert saved_issue["impact"] == impact
        assert saved_issue["solution"] == solution
        assert saved_issue["remarks"] == remarks
        assert saved_issue["related_subtasks"] == related_subtasks
        assert "created_at" in saved_issue
    
    def test_save_issue_update(self, file_manager):
        """課題ファイルの更新機能をテスト"""
        task_id = "test-task-006"

        # 初期の課題を保存
        file_path1, initial_issue_id = file_manager.save_issue(
            task_id=task_id, issue_id=None, status="open", description="初期課題",
            impact="low", solution="策1", remarks=None, related_subtasks=[]
        )

        # 課題を更新
        updated_description = "更新された課題"
        updated_status = "closed"
        file_path2, updated_issue_id = file_manager.save_issue(
            task_id=task_id,
            issue_id=initial_issue_id, # 更新対象のIDを指定
            status=updated_status,
            description=updated_description,
            impact="low", # 他のフィールドは変えない
            solution="策1",
            remarks="解決済み", # remarksを追加
            related_subtasks=[]
        )

        assert file_path1 == file_path2
        assert initial_issue_id == updated_issue_id

        # 更新されたファイルを確認
        loaded_data: IssueFileData = file_manager.load_issues(task_id)
        assert len(loaded_data["issues"]) == 1 # 課題数は増えていない
        updated_issue_data = loaded_data["issues"][0]
        assert updated_issue_data["issue_id"] == initial_issue_id
        assert updated_issue_data["description"] == updated_description
        assert updated_issue_data["status"] == updated_status
        assert updated_issue_data["remarks"] == "解決済み"
        # created_at は最初のままのはず
        initial_load = yaml.safe_load(Path(file_path1).read_text(encoding='utf-8'))
        assert updated_issue_data["created_at"] == initial_load["issues"][0]["created_at"]
    
    def test_save_issue_add_multiple(self, file_manager):
        """複数の課題を追加する機能をテスト"""
        task_id = "test-task-007"

        # 1つ目の課題を追加
        _, id1 = file_manager.save_issue(
            task_id=task_id, issue_id=None, status="open", description="課題1",
            impact="high", solution="未定", remarks=None, related_subtasks=["s1"]
        )

        # 2つ目の課題を追加
        _, id2 = file_manager.save_issue(
            task_id=task_id, issue_id=None, status="investigating", description="課題2",
            impact="medium", solution="調査中", remarks="要確認", related_subtasks=["s2"]
        )

        assert id1 != id2

        # ファイルを確認
        loaded_data: IssueFileData = file_manager.load_issues(task_id)
        assert len(loaded_data["issues"]) == 2
        descriptions = {issue["description"] for issue in loaded_data["issues"]}
        assert "課題1" in descriptions
        assert "課題2" in descriptions
        issue_ids = {issue["issue_id"] for issue in loaded_data["issues"]}
        assert id1 in issue_ids
        assert id2 in issue_ids
    
    def test_delete_plan(self, file_manager):
        """プラン削除機能をテスト"""
        plan_id = "test-plan-004"
        task_id = "task-for-delete"
        subtasks: List[Subtask] = [{"id":"s1", "description":"d", "status":"p", "order":1, "inputs":[], "outputs":[]}]

        # 初期バージョンを保存
        file_manager.save_plan(plan_id, task_id, "initial", subtasks)

        # 2つ目のバージョンを保存（履歴を作成）
        file_manager.save_plan(plan_id, task_id, "updated", subtasks)

        # プランが存在することを確認
        plan_file = file_manager.plans_dir / f"{plan_id}.yaml"
        history_dir = file_manager.history_dir / plan_id
        assert plan_file.exists()
        assert history_dir.exists()
        assert len(list(history_dir.glob("v*_*.yaml"))) > 0

        # プランを削除
        result = file_manager.delete_plan(plan_id)

        # 削除が成功したことを確認
        assert result is True

        # ファイルと履歴ディレクトリが削除されたことを確認
        assert not plan_file.exists()
        assert not history_dir.exists() 