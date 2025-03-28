import pytest
from typing import Dict, Any, List
import yaml
from planning_agent.data.plan_data import PlanData

def test_create_plan_data():
    """基本的なプランデータの作成テスト"""
    data = {
        "id": "PLAN001",
        "title": "テストプラン",
        "description": "これはテスト用のプランです",
        "status": "draft",
        "steps": [
            {"order": 1, "action": "ステップ1", "description": "最初のステップ"},
            {"order": 2, "action": "ステップ2", "description": "次のステップ"}
        ]
    }
    plan = PlanData(**data)
    assert plan.id == "PLAN001"
    assert plan.title == "テストプラン"
    assert plan.description == "これはテスト用のプランです"
    assert plan.status == "draft"
    assert len(plan.steps) == 2
    assert plan.steps[0]["order"] == 1
    assert plan.steps[1]["action"] == "ステップ2"

def test_plan_data_validation():
    """必須フィールドの検証テスト"""
    with pytest.raises(ValueError):
        PlanData()  # 必須フィールドなしで作成

    with pytest.raises(ValueError):
        PlanData(id="PLAN001")  # 一部の必須フィールドが欠落

def test_plan_data_serialization():
    """YAMLシリアライズ/デシリアライズテスト"""
    data = {
        "id": "PLAN001",
        "title": "テストプラン",
        "description": "これはテスト用のプランです",
        "status": "draft",
        "steps": [
            {"order": 1, "action": "ステップ1", "description": "最初のステップ"},
            {"order": 2, "action": "ステップ2", "description": "次のステップ"}
        ],
        "metadata": {
            "created_at": "2024-03-27",
            "created_by": "test_user"
        }
    }
    plan = PlanData(**data)
    
    # シリアライズ
    yaml_str = yaml.dump(plan.to_dict())
    
    # デシリアライズ
    loaded_data = yaml.safe_load(yaml_str)
    loaded_plan = PlanData(**loaded_data)
    
    assert loaded_plan.id == plan.id
    assert loaded_plan.title == plan.title
    assert loaded_plan.description == plan.description
    assert loaded_plan.status == plan.status
    assert len(loaded_plan.steps) == len(plan.steps)
    assert loaded_plan.metadata == plan.metadata

def test_plan_data_step_validation():
    """ステップデータの検証テスト"""
    with pytest.raises(ValueError):
        PlanData(
            id="PLAN001",
            title="テストプラン",
            description="テスト",
            status="draft",
            steps=[
                {"order": 1}  # 必須フィールドの欠落
            ]
        )

    with pytest.raises(ValueError):
        PlanData(
            id="PLAN001",
            title="テストプラン",
            description="テスト",
            status="draft",
            steps=[
                {"order": 1, "action": "ステップ1", "description": "説明1"},
                {"order": 1, "action": "ステップ2", "description": "説明2"}  # 重複するorder
            ]
        )

def test_plan_data_status_transitions():
    """ステータス遷移のテスト"""
    plan = PlanData(
        id="PLAN001",
        title="テストプラン",
        description="テスト",
        status="draft",
        steps=[{"order": 1, "action": "ステップ1", "description": "説明"}]
    )
    
    # 有効なステータス遷移
    plan.status = "in_progress"
    assert plan.status == "in_progress"
    
    plan.status = "completed"
    assert plan.status == "completed"
    
    # 無効なステータス遷移
    with pytest.raises(ValueError):
        plan.status = "invalid_status"

def test_plan_data_step_ordering():
    """ステップの順序付けテスト"""
    steps = [
        {"order": 2, "action": "ステップ2", "description": "説明2"},
        {"order": 1, "action": "ステップ1", "description": "説明1"},
        {"order": 3, "action": "ステップ3", "description": "説明3"}
    ]
    
    plan = PlanData(
        id="PLAN001",
        title="テストプラン",
        description="テスト",
        status="draft",
        steps=steps
    )
    
    # ステップが順序通りにソートされていることを確認
    assert plan.steps[0]["order"] == 1
    assert plan.steps[1]["order"] == 2
    assert plan.steps[2]["order"] == 3 