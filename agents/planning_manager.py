import os
from dotenv import load_dotenv
from smolagents import CodeAgent, LiteLLMModel
from utils import tools  # utils/__init__.py で公開されているツールをインポート
import json # 結果パース用 (将来的にAgent内で使う可能性も考慮)

# 環境変数の読み込み (APIキーなどを想定)
load_dotenv()

# CodeAgent がコード実行時にインポートを許可するライブラリのリスト
AUTHORIZED_IMPORTS = [
    "yaml",
    "datetime",
    "pathlib",
    "typing",
    "json", # JSON操作用
    # 必要に応じて他の安全なライブラリを追加
]

def create_planning_manager_agent(model_id: str = "gpt-4o") -> CodeAgent:
    """
    PlanningManagerAgent (CodeAgent) のインスタンスを作成して返します。

    Args:
        model_id (str): 使用するLLMのモデルID (デフォルト: "gpt-4o")

    Returns:
        CodeAgent: 初期化されたPlanningManagerAgentインスタンス
    """
    # LLMモデルの初期化 (LiteLLMを使用)
    # 必要に応じて max_completion_tokens などを設定
    # 注意: LiteLLMModelを使用するには、適切な環境変数 (例: OPENAI_API_KEY) が設定されている必要があります。
    model_params = {
        "model_id": model_id,
        # "max_completion_tokens": 4096, # 必要に応じて設定
    }
    model = LiteLLMModel(**model_params)

    # エージェントが使用するツールのリスト
    available_tools = [
        tools.save_yaml, tools.load_yaml,
        tools.save_requirements, tools.load_requirements,
        tools.save_plan, tools.load_plan,
        tools.save_issue, tools.load_issues,
        tools.list_plans, tools.list_requirements,
        tools.backup_plan, tools.delete_plan
    ]

    # 将来的に追加する他の専門エージェント (ManagedAgent) のリスト
    managed_agents = []

    # CodeAgentの初期化
    agent = CodeAgent(
        model=model,
        tools=available_tools,
        managed_agents=managed_agents, # 現時点では空リスト
        additional_authorized_imports=AUTHORIZED_IMPORTS,
        verbosity_level=2,  # ログの詳細度 (0:静か, 1:INFO, 2:DEBUG)
        max_steps=10,       # エージェントの最大思考ステップ数
        # planning_interval や他のパラメータは必要に応じて調整
    )

    return agent
