import pytest
import yaml
import tempfile
import os
from planning_agent.data.requirement_data import RequirementData
from planning_agent.data.plan_data import PlanData

def test_requirement_plan_integration():
    """要件データとプランデータの連携テスト"""
    # 要件データの作成
    requirement = RequirementData(
        id="REQ001",
        title="テスト要件",
        description="これはテスト用の要件です",
        priority="high",
        status="open"
    )
    
    # 要件に基づくプランの作成
    plan = PlanData(
        id="PLAN001",
        title=f"要件 {requirement.id} の実装プラン",
        description=f"要件「{requirement.title}」の実装計画",
        status="draft",
        steps=[
            {
                "order": 1,
                "action": "要件分析",
                "description": "要件の詳細分析を行う"
            },
            {
                "order": 2,
                "action": "実装",
                "description": "要件に基づいて実装を行う"
            }
        ],
        metadata={
            "requirement_id": requirement.id,
            "priority": requirement.priority
        }
    )
    
    # 関連付けの検証
    assert plan.metadata["requirement_id"] == requirement.id
    assert plan.metadata["priority"] == requirement.priority

def test_yaml_file_io():
    """YAMLファイルの入出力テスト"""
    # テストデータの作成
    requirement = RequirementData(
        id="REQ001",
        title="テスト要件",
        description="これはテスト用の要件です",
        priority="high",
        status="open"
    )
    
    plan = PlanData(
        id="PLAN001",
        title="テストプラン",
        description="これはテスト用のプランです",
        status="draft",
        steps=[
            {
                "order": 1,
                "action": "ステップ1",
                "description": "最初のステップ"
            }
        ]
    )
    
    # 一時ファイルの作成とテスト
    with tempfile.TemporaryDirectory() as temp_dir:
        req_file = os.path.join(temp_dir, "requirement.yaml")
        plan_file = os.path.join(temp_dir, "plan.yaml")
        
        # ファイルへの書き込み
        with open(req_file, "w") as f:
            yaml.dump(requirement.to_dict(), f)
        
        with open(plan_file, "w") as f:
            yaml.dump(plan.to_dict(), f)
        
        # ファイルからの読み込み
        with open(req_file, "r") as f:
            loaded_req_data = yaml.safe_load(f)
            loaded_req = RequirementData(**loaded_req_data)
        
        with open(plan_file, "r") as f:
            loaded_plan_data = yaml.safe_load(f)
            loaded_plan = PlanData(**loaded_plan_data)
        
        # データの検証
        assert loaded_req.id == requirement.id
        assert loaded_req.title == requirement.title
        assert loaded_plan.id == plan.id
        assert loaded_plan.steps == plan.steps

def test_complex_data_structure():
    """複雑なデータ構造の統合テスト"""
    # 複数の要件とそれに紐づくプランのテスト
    requirements = [
        RequirementData(
            id=f"REQ00{i}",
            title=f"要件{i}",
            description=f"これは要件{i}の説明です",
            priority="high" if i == 1 else "medium",
            status="open"
        ) for i in range(1, 4)
    ]
    
    plans = []
    for req in requirements:
        plan = PlanData(
            id=f"PLAN_{req.id}",
            title=f"{req.title}の実装プラン",
            description=f"{req.description}に基づく実装計画",
            status="draft",
            steps=[
                {
                    "order": 1,
                    "action": "分析",
                    "description": f"{req.title}の分析"
                },
                {
                    "order": 2,
                    "action": "実装",
                    "description": f"{req.title}の実装"
                }
            ],
            metadata={"requirement_id": req.id}
        )
        plans.append(plan)
    
    # データの検証
    assert len(requirements) == len(plans)
    for req, plan in zip(requirements, plans):
        assert plan.metadata["requirement_id"] == req.id
        assert req.title in plan.title  # IDではなくタイトルを確認 