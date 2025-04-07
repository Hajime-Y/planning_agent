import pytest
from unittest.mock import patch, MagicMock

# テスト対象の関数をインポート
from agents.planning_manager import create_planning_manager_agent, AUTHORIZED_IMPORTS

# smolagents のクラスをインポート (型チェックや isinstance で使用)
from smolagents import CodeAgent, LiteLLMModel

# FinalAnswerTool をインポート
from smolagents.default_tools import FinalAnswerTool

# utils.tools 内のツール関数をインポート (比較用)
from utils import tools

# --- テストケース --- 

# モック設定: LiteLLMModel の初期化をモック化 (APIキーなしでテストするため)
@patch('agents.planning_manager.LiteLLMModel', return_value=MagicMock(spec=LiteLLMModel))
def test_create_agent_instance(mock_lite_llm_model):
    """create_planning_manager_agentがCodeAgentインスタンスを返すことを確認"""
    agent = create_planning_manager_agent()
    assert isinstance(agent, CodeAgent)
    # LiteLLMModelのモックが呼び出されたことを確認
    mock_lite_llm_model.assert_called_once()

@patch('agents.planning_manager.LiteLLMModel', return_value=MagicMock(spec=LiteLLMModel))
def test_agent_has_tools(mock_lite_llm_model):
    """生成されたエージェントが期待されるツールを持っているか確認"""
    agent = create_planning_manager_agent()
    
    # utils.tools から公開されているツールオブジェクトのリストを取得
    # Note: tools モジュール内の SimpleTool インスタンスを直接参照する
    expected_user_tools_objects = [
        tools.save_yaml, tools.load_yaml,
        tools.save_requirements, tools.load_requirements,
        tools.save_plan, tools.load_plan,
        tools.save_issue, tools.load_issues,
        tools.list_plans, tools.list_requirements,
        tools.backup_plan, tools.delete_plan
    ]
    
    # smolagentsがデフォルトで追加するツールも考慮
    
    # エージェントのツールを名前で取得
    agent_tool_names = set(agent.tools.keys())
    
    # 期待されるユーザーツールの名前リスト (SimpleToolオブジェクトのname属性から取得)
    expected_user_tool_names = set(tool_obj.name for tool_obj in expected_user_tools_objects)
    
    # デフォルトで追加される可能性のあるツール名
    default_tool_name = "final_answer" # FinalAnswerToolのデフォルト名と仮定
    
    # 期待される全ツール名セット
    expected_all_tool_names = expected_user_tool_names | {default_tool_name}
    
    # ツール名のセットが一致するか確認
    assert agent_tool_names == expected_all_tool_names
    
    # (オプション) ツールの数も確認
    assert len(agent.tools) == len(expected_all_tool_names)

@patch('agents.planning_manager.LiteLLMModel', return_value=MagicMock(spec=LiteLLMModel))
def test_agent_model_type(mock_lite_llm_model):
    """生成されたエージェントのモデルがLiteLLMModelであることを確認"""
    agent = create_planning_manager_agent()
    # agent.model はモック化された LiteLLMModel インスタンスのはず
    assert isinstance(agent.model, MagicMock) 
    # specのチェック方法を修正
    assert agent.model._spec_class == LiteLLMModel 

@patch('agents.planning_manager.LiteLLMModel', return_value=MagicMock(spec=LiteLLMModel))
def test_authorized_imports(mock_lite_llm_model):
    """エージェントに期待されるadditional_authorized_importsが設定されているか確認"""
    agent = create_planning_manager_agent()
    # agents.planning_manager で定義されているリストと比較
    assert agent.additional_authorized_imports == AUTHORIZED_IMPORTS

# --- 必要に応じて他のテストケースを追加 --- 
