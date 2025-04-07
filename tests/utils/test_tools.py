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

# utils.tools からテスト対象のツールと必要な型をインポート
from utils.tools import (
    save_requirements, load_requirements,
    save_plan, load_plan,
    save_issue, load_issues,
)
# FileManager や TypedDict はテストロジックでは直接使わないが、
# utils.tools が内部で使うため、間接的に必要になる可能性がある
# (特に setup_file_manager フィクスチャ)
from utils.file_manager import FileManager


class TestTools:
    """Smolagentsツールのテスト"""

    # temp_dir フィクスチャは不要になったため削除

    @pytest.fixture
    def setup_file_manager(self, monkeypatch):
        """FileManagerのインスタンスを一時ディレクトリを使うようにパッチする"""
        temp_dir = tempfile.mkdtemp()

        # ツールモジュール内の_file_managerを一時ディレクトリを使うインスタンスに置き換える
        import utils.tools
        # _file_manager を直接パッチする
        monkeypatch.setattr(utils.tools, "_file_manager", FileManager(base_dir=temp_dir))

        yield temp_dir # 一時ディレクトリのパスを返す (ファイルパス確認用)

        # テスト終了後にディレクトリを削除
        shutil.rmtree(temp_dir)

    # test_save_and_load_yaml は削除

    def test_save_and_load_requirements(self, setup_file_manager):
        """save_requirementsとload_requirementsツールのテスト"""
        base_dir = setup_file_manager # フィクスチャから一時ディレクトリパスを取得
        task_id = "test-task-101"
        title = "ツールテスト"
        description = "要件ツールのテスト"
        constraints = ["制約A"]
        resources = ["リソースX"]

        # 保存 (clarificationsは削除されたので渡さない)
        result_message = save_requirements(
            task_id=task_id,
            title=title,
            description=description,
            constraints=constraints,
            resources=resources,
        )
        expected_path = Path(base_dir) / "requirements" / f"{task_id}.yaml"
        assert result_message == str(expected_path) # 保存パスが返ることを確認
        assert expected_path.exists()

        # 読み込み
        loaded = load_requirements(task_id)
        assert loaded["title"] == title
        assert loaded["description"] == description
        assert loaded["constraints"] == constraints
        assert loaded["resources"] == resources
        assert loaded["task_id"] == task_id
        assert "created_at" in loaded
        assert "updated_at" in loaded

    def test_save_and_load_plan(self, setup_file_manager):
        """save_planとload_planツールのテスト"""
        base_dir = setup_file_manager
        plan_id = "test-plan-101"
        task_id = "linked-task-id"
        status = "pending"
        subtasks = [{"id": "sub1", "description": "サブタスク1", "status": "pending", "order": 1, "inputs": [], "outputs": []}]

        # 保存
        result_message = save_plan(
            plan_id=plan_id,
            task_id=task_id,
            status=status,
            subtasks=subtasks,
        )
        expected_path = Path(base_dir) / "plans" / f"{plan_id}.yaml"
        assert f"プランを保存しました: {expected_path} (バージョン: 1)" in result_message

        # 読み込み
        loaded = load_plan(plan_id)
        assert loaded["task_id"] == task_id
        assert loaded["status"] == status
        assert loaded["subtasks"][0]["id"] == "sub1"
        assert loaded["version"] == 1
        assert "created_at" in loaded
        assert "updated_at" in loaded

    def test_save_and_load_issues(self, setup_file_manager):
        """save_issueとload_issuesツールのテスト (新規作成)"""
        base_dir = setup_file_manager
        task_id = "test-task-102"
        description = "課題ツールのテスト"
        status = "open"
        impact = "medium"
        solution = "解決策1"
        remarks = None
        related_subtasks = ["subtask-related"]

        # 保存 (issue_id=None で新規作成)
        result_message = save_issue(
            task_id=task_id,
            issue_id=None,
            status=status,
            description=description,
            impact=impact,
            solution=solution,
            remarks=remarks,
            related_subtasks=related_subtasks,
        )
        expected_path = Path(base_dir) / "issues" / f"{task_id}.yaml"
        assert expected_path.exists()
        # Issue ID は自動生成されるので、メッセージの形式で確認
        assert f"課題 'issue-{task_id}-001' を保存しました: {expected_path}" in result_message

        # 読み込み
        loaded = load_issues(task_id)
        assert loaded["task_id"] == task_id
        assert len(loaded["issues"]) == 1
        issue = loaded["issues"][0]
        assert issue["issue_id"] == f"issue-{task_id}-001"
        assert issue["description"] == description
        assert issue["status"] == status
        assert issue["impact"] == impact
        assert issue["solution"] == solution
        assert issue["remarks"] == remarks
        assert issue["related_subtasks"] == related_subtasks
        assert "created_at" in issue
        assert "updated_at" in loaded # ファイル全体の更新日時

    # test_list_plans_and_requirements は削除
    # test_backup_and_delete_plan は削除 