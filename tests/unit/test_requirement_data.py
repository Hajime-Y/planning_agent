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
        RequirementData()  # 必須フィールドなしで作成

    with pytest.raises(ValueError):
        RequirementData(id="REQ001")  # 一部の必須フィールドが欠落

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