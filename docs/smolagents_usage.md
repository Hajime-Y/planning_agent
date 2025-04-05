# Smolagentsフレームワーク 使用方法ガイド

## 1. Smolagentsとは

Smolagentsは、Hugging Face社が開発した「シンプルさ」を重視したAIエージェントフレームワークです。「smolagents」という名前の「smol」は「small（小さい）」を意味し、最小限の抽象化とシンプルなAPIで強力なAIエージェントの構築を可能にします。

AIエージェントとは、LLM（大規模言語モデル）の出力によってワークフローが制御されるプログラムのことです。通常のLLMを使ったアプリケーションとの違いは、エージェントが「考えて」「行動する」という自律的なプロセスを繰り返すことができる点にあります。

## 2. Smolagentsの基本コンセプト

### 2.1 主な特徴

- **シンプルなコードベース**: 約1,000行の中核コード（`agents.py`）で実装されており、抽象化を最小限に抑えています
- **コードベースのエージェント**: 従来のJSON形式でのツール呼び出しではなく、Pythonコードを生成・実行することでアクションを実行します
- **どんなLLMでも使用可能**: Hugging Face Hub上のモデル、OpenAI、Anthropic、その他多くのモデルと互換性があります
- **安全なコード実行**: E2BやDockerなどのサンドボックス環境でのコード実行をサポートしています
- **マルチモーダル対応**: テキストだけでなく、画像、動画、音声などの入力にも対応しています

### 2.2 主要なエージェントタイプ

1. **CodeAgent**: 
   - Pythonコードを直接生成・実行するエージェント
   - より効率的な問題解決が可能（JSON形式の処理と比較して約30%のステップ削減）
   - 複雑なロジックも簡単に表現できる

2. **ToolCallingAgent**: 
   - 従来型のJSON/テキストブロックでアクションを記述するエージェント
   - コード実行が不要または望ましくない場合に適している

3. **ManagedAgent**: 
   - 他のエージェントをラップし、マルチエージェントシステムの構築に使用
   - 階層的なエージェント構造を作成する際に利用される

## 3. エージェントの作成方法

### 3.1 基本的なエージェントの作成

Smolagentsでエージェントを作成するには、最低限以下の2つの要素が必要です：

1. **model**: エージェントを駆動するLLM
2. **tools**: エージェントが使用するツール（機能）のリスト

```python
# 基本的なエージェントの作成例
from smolagents import CodeAgent, HfApiModel, DuckDuckGoSearchTool

# 1. モデルの初期化（Hugging Face APIを使用）
model = HfApiModel()  # デフォルトでは無料で使用可能なモデルが選択される

# 2. ツールの準備（この例ではウェブ検索ツール）
tools = [DuckDuckGoSearchTool()]

# 3. エージェントの初期化
agent = CodeAgent(
    tools=tools, 
    model=model
)

# 4. エージェントの実行
result = agent.run("東京の今日の天気を調べて教えてください")
print(result)
```

### 3.2 カスタムツールの作成

ツールとは、エージェントが使用できる機能（関数）のことです。カスタムツールは以下のように作成できます：

```python
from smolagents import tool

@tool
def weather_tool(location: str, date: str = "today") -> str:
    """特定の場所と日付の天気を取得します。
    
    Args:
        location: 天気を調べる地名（例: 東京、大阪）
        date: 天気を調べる日付（デフォルト: 今日）
    
    Returns:
        天気情報の文字列
    """
    # 実際にはここで天気APIを呼び出すなどの処理
    # この例ではダミーデータを返します
    return f"{location}の{date}の天気は晴れです。気温は25度の予想です。"
```

ツールの作成には以下の要素が重要です：
- 関数名: ツールの名前として使用されます
- 型ヒント: 引数の型と戻り値の型を示します
- ドキュメント文字列: ツールの説明と引数の説明を含む必要があります

### 3.3 モデルの選択

Smolagentsは様々なLLMモデルをサポートしています：

```python
# Hugging Face Hubのモデルを使用（無料・有料）
from smolagents import HfApiModel
model = HfApiModel(model_id="meta-llama/Llama-2-70b-chat-hf")

# OpenAI、Anthropicなど多くのプロバイダーのモデルを使用
from smolagents import LiteLLMModel
model = LiteLLMModel(model_id="gpt-4")

# ローカルで実行するTransformersモデル
from smolagents import TransformersModel
from transformers import pipeline
pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")
model = TransformersModel(pipe)
```

## 4. マルチエージェントシステムの構築

複数のエージェントが協力して問題を解決するマルチエージェントシステムは、以下のように構築できます：

```python
from smolagents import CodeAgent, HfApiModel, DuckDuckGoSearchTool, ManagedAgent

# LLMモデルの初期化
model = HfApiModel()

# 専用エージェントの作成
web_agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
    name="web_search",
    description="ウェブ検索を実行します。検索クエリを引数として渡してください。"
)

# マネージドエージェントとして登録
managed_web_agent = ManagedAgent(
    agent=web_agent,
    name="web_search",
    description="ウェブ検索を実行します。検索クエリを引数として渡してください。"
)

# マネージャーエージェントの作成
manager_agent = CodeAgent(
    tools=[],  # 必要に応じてツールを追加
    model=model,
    managed_agents=[managed_web_agent]
)

# マネージャーエージェントを実行
result = manager_agent.run("ノーベル物理学賞2023年の受賞者は誰ですか？")
```

このようにして、特定のタスクに特化した個別のエージェントを作成し、それらを統括するマネージャーエージェントを構築することで、効率的な分業システムを実現できます。

## 5. インターフェースの実装

### 5.1 コマンドラインインターフェース

シンプルなコマンドラインインターフェースは以下のように実装できます：

```python
from smolagents import CodeAgent, HfApiModel

def run_cli():
    """コマンドラインインターフェースを実行します"""
    model = HfApiModel()
    
    # エージェントの初期化
    agent = CodeAgent(
        tools=[],  # 必要なツールを追加
        model=model,
        add_base_tools=True  # デフォルトのツール（ウェブ検索など）を追加
    )
    
    # 対話ループ
    print("エージェントに質問してください（終了するには 'quit' と入力）")
    while True:
        user_input = input("> ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
            
        result = agent.run(user_input)
        print(f"\n{result}\n")

if __name__ == "__main__":
    run_cli()
```

### 5.2 Webインターフェース（Gradio）

Gradioを使ったWebインターフェースは以下のように簡単に実装できます：

```python
from smolagents import CodeAgent, HfApiModel, GradioUI

def run_web_interface():
    """Webインターフェースを起動します"""
    model = HfApiModel()
    
    # エージェントの初期化
    agent = CodeAgent(
        tools=[],  # 必要なツールを追加
        model=model,
        add_base_tools=True  # デフォルトのツール（ウェブ検索など）を追加
    )
    
    # Gradioインターフェースの起動
    GradioUI(agent).launch()

if __name__ == "__main__":
    run_web_interface()
```

実行すると、デフォルトでは`http://localhost:7860`でWebインターフェースにアクセスできます。

## 6. セキュリティとエラー処理

### 6.1 セキュア実行環境

CodeAgentでは、生成されたコードが実行されるため、セキュリティに注意が必要です：

```python
# E2Bサンドボックスを使用する場合（推奨）
agent = CodeAgent(
    tools=tools,
    model=model,
    executor_type="e2b"  # E2B環境変数の設定も必要
)

# Dockerサンドボックスを使用する場合
agent = CodeAgent(
    tools=tools,
    model=model,
    executor_type="docker"
)
```

### 6.2 安全なインポート

デフォルトでは限られたPythonモジュールのみインポートが許可されています。追加のモジュールを許可するには：

```python
agent = CodeAgent(
    tools=tools,
    model=model,
    additional_authorized_imports=["numpy", "pandas", "matplotlib.pyplot"]
)
```

## 7. まとめ

Smolagentsは、シンプルさと効率性を重視したエージェントフレームワークです。その特徴は以下の通りです：

- シンプルなAPIでありながら強力な機能を提供
- コードベースのエージェントによる高効率な処理
- 様々なLLMモデルとの互換性
- マルチエージェントシステムの構築サポート
- 安全なコード実行環境の提供

「Planning Agent」プロジェクトでは、Smolagentsのこれらの特徴を活用して、効率的なタスク分解と具体的なプラン生成を実現します。

## 8. 参考リンク

より詳細な情報は以下のリソースを参照してください：

- [Smolagents公式ドキュメント](https://huggingface.co/docs/smolagents)
- [Smolagents GitHub リポジトリ](https://github.com/huggingface/smolagents)
- [Hugging Face ブログ：Smolagentsの紹介](https://huggingface.co/blog/smolagents)

さらに詳細な情報やサンプルコードについては、playwright mcpを使って調査することができます。エージェントフレームワークは急速に発展している分野ですので、最新情報を確認するようにしてください。 