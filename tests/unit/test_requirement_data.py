import pytest
from typing import Dict, Any
import yaml
from planning_agent.data.requirement_data import RequirementData

def test_create_requirement_data():
    """基本的な要件データの作成テスト"""
    data = {
        "id": "REQ001",
        "title": "テスト要件",
        "description": "これはテスト用の要件です",
        "priority": "high",
        "status": "open"
    }
    req = RequirementData(**data)
    assert req.id == "REQ001"
    assert req.title == "テスト要件"
    assert req.description == "これはテスト用の要件です"
    assert req.priority == "high"
    assert req.status == "open"

def test_requirement_data_validation():
    """必須フィールドの検証テスト"""
    with pytest.raises(ValueError):
        RequirementData(
            id="",  # 空のID
            title="テスト",
            description="説明",
            priority="high",
            status="open"
        )

    with pytest.raises(ValueError):
        RequirementData(
            id="REQ001",
            title="",  # 空のタイトル
            description="説明",
            priority="high",
            status="open"
        )

def test_requirement_data_serialization():
    """YAMLシリアライズ/デシリアライズテスト"""
    data = {
        "id": "REQ001",
        "title": "テスト要件",
        "description": "これはテスト用の要件です",
        "priority": "high",
        "status": "open",
        "tags": ["test", "sample"],
        "metadata": {"created_by": "test_user"}
    }
    req = RequirementData(**data)
    
    # シリアライズ
    yaml_str = yaml.dump(req.to_dict())
    
    # デシリアライズ
    loaded_data = yaml.safe_load(yaml_str)
    loaded_req = RequirementData(**loaded_data)
    
    assert loaded_req.id == req.id
    assert loaded_req.title == req.title
    assert loaded_req.description == req.description
    assert loaded_req.priority == req.priority
    assert loaded_req.status == req.status
    assert loaded_req.tags == req.tags
    assert loaded_req.metadata == req.metadata

def test_requirement_data_edge_cases():
    """エッジケースのテスト"""
    # 空の説明
    req = RequirementData(
        id="REQ001",
        title="テスト要件",
        description="",
        priority="low",
        status="open"
    )
    assert req.description == ""

    # 特殊文字を含むデータ
    special_chars = "特殊文字!@#$%^&*()_+"
    req = RequirementData(
        id="REQ001",
        title=special_chars,
        description="テスト",
        priority="medium",
        status="open"
    )
    assert req.title == special_chars

def test_requirement_data_invalid_priority():
    """無効な優先度値のテスト"""
    with pytest.raises(ValueError):
        RequirementData(
            id="REQ001",
            title="テスト要件",
            description="テスト",
            priority="invalid_priority",  # 無効な優先度
            status="open"
        )

def test_requirement_data_invalid_status():
    """無効なステータス値のテスト"""
    with pytest.raises(ValueError):
        RequirementData(
            id="REQ001",
            title="テスト要件",
            description="テスト",
            priority="high",
            status="invalid_status"  # 無効なステータス
        )

def test_requirement_data_from_dict():
    """from_dictメソッドのテスト"""
    data = {
        "id": "test_id",
        "title": "Test Requirement",
        "description": "Test Description",
        "priority": "high",
        "status": "open",
        "tags": ["test", "sample"],
        "metadata": {"key": "value"}
    }
    requirement = RequirementData.from_dict(data)
    assert requirement.id == "test_id"
    assert requirement.title == "Test Requirement"
    assert requirement.description == "Test Description"
    assert requirement.priority == "high"
    assert requirement.status == "open"
    assert requirement.tags == ["test", "sample"]
    assert requirement.metadata == {"key": "value"}

def test_requirement_data_constraints():
    """制約条件フィールドのテスト"""
    constraints = ["期限は2024年4月末まで", "予算上限は100万円"]
    req = RequirementData(
        id="REQ001",
        title="テスト要件",
        description="テスト",
        priority="high",
        status="open",
        constraints=constraints
    )
    assert req.constraints == constraints
    
    # to_dictメソッドでの出力確認
    data_dict = req.to_dict()
    assert "constraints" in data_dict
    assert data_dict["constraints"] == constraints

def test_requirement_data_completion_criteria():
    """完了判定基準フィールドのテスト"""
    criteria = ["全機能がテストされていること", "コードカバレッジ80%以上", "セキュリティスキャンでの脆弱性ゼロ"]
    req = RequirementData(
        id="REQ001",
        title="テスト要件",
        description="テスト",
        priority="high",
        status="open",
        completion_criteria=criteria
    )
    assert req.completion_criteria == criteria
    
    # to_dictメソッドでの出力確認
    data_dict = req.to_dict()
    assert "completion_criteria" in data_dict
    assert data_dict["completion_criteria"] == criteria

def test_requirement_data_all_fields():
    """全フィールドを含む完全なオブジェクトのテスト"""
    data = {
        "id": "REQ001",
        "title": "完全なテスト要件",
        "description": "すべてのフィールドを含むテスト",
        "priority": "high",
        "status": "in_progress",
        "constraints": ["制約1", "制約2"],
        "completion_criteria": ["基準1", "基準2", "基準3"],
        "tags": ["重要", "フロントエンド"],
        "metadata": {"作成者": "テストユーザー", "作成日": "2024-03-28"}
    }
    
    req = RequirementData(**data)
    
    # すべてのフィールドが正しく設定されていることを確認
    assert req.id == data["id"]
    assert req.title == data["title"]
    assert req.description == data["description"]
    assert req.priority == data["priority"]
    assert req.status == data["status"]
    assert req.constraints == data["constraints"]
    assert req.completion_criteria == data["completion_criteria"]
    assert req.tags == data["tags"]
    assert req.metadata == data["metadata"]
    
    # シリアライズ後のデシリアライズでも全フィールドが保持されていることを確認
    serialized = yaml.dump(req.to_dict())
    deserialized = RequirementData.from_dict(yaml.safe_load(serialized))
    
    assert deserialized.id == req.id
    assert deserialized.title == req.title
    assert deserialized.constraints == req.constraints
    assert deserialized.completion_criteria == req.completion_criteria 