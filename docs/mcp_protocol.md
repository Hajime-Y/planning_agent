# MCPプロトコル調査

## 1. 概要

MCP (Model Context Protocol) は、複数のAIエージェントが連携してタスクを実行するためのプロトコルです。本ドキュメントでは、MCPプロトコルの仕様、関連技術、およびClaudeとの連携方法について調査した結果をまとめます。

MCPは、USBポートがさまざまな周辺機器に接続するための標準規格を提供するように、AIモデルが異なるデータソースやツールに接続するための標準化された方法を提供します。これにより、LLM（大規模言語モデル）がデータや外部ツールと統合し、エージェントや複雑なワークフローを構築することが容易になります。

## 2. OpenAI Agent SDK の調査

OpenAI Agent SDKは、エージェントAIアプリケーションを構築するための軽量かつ使いやすいパッケージです。このSDKは、以前の実験的なエージェントフレームワークである「Swarm」の本番環境向け改良版として位置づけられています。

### 2.1 基本概念

OpenAI Agent SDKは、以下の主要な要素で構成されています：

1. **エージェント（Agents）**: 命令とツールを装備したLLM
2. **ハンドオフ（Handoffs）**: エージェントが特定のタスクを他のエージェントに委任する機能
3. **ガードレール（Guardrails）**: エージェントへの入力を検証する機能

### 2.2 Claude 3.7 Sonnetとの統合

Agent SDKを使用してClaude 3.7 Sonnetを統合するには、以下の方法があります：

1. **カスタムモデルの設定**:
   OpenAI Agent SDKは、OpenAI以外のLLMプロバイダーとも連携可能です。Claude 3.7 Sonnetを使用するには、以下のパターンが利用できます：

```python
import asyncio
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled

# Anthropic APIのベースURLとAPI Keyを設定
BASE_URL = "https://api.anthropic.com/v1"
API_KEY = "your_anthropic_api_key"
MODEL_NAME = "claude-3-7-sonnet-20240307"

# カスタムOpenAIクライアントの作成
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

# トレーシングの無効化（必要に応じて）
set_tracing_disabled(disabled=True)

async def main():
    # このエージェントはカスタムLLMプロバイダー（Claude）を使用
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
        model=OpenAIChatCompletionsModel(
            model=MODEL_NAME,
            openai_client=client
        ),
    )
    
    result = await Runner.run(agent, "Hello, how are you?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

2. **注意点**:
   - Responses APIとChat Completions APIのどちらを使用するかは、LLMプロバイダーのサポート状況によります
   - ほとんどのLLMプロバイダーはChat Completions APIのみをサポートしているため、Claudeの場合も`OpenAIChatCompletionsModel`を使用することが推奨されます
   - 構造化出力（JSON形式など）のサポートはプロバイダーによって異なります

## 3. MCPプロトコルの仕様調査

### 3.1 MCPの基本アーキテクチャ

MCPはクライアント-サーバーアーキテクチャに基づいており、ホストアプリケーションが複数のサーバーに接続できます：

1. **MCPホスト**: Claude Desktop、IDE、AIツールなど、MCPを通じてデータにアクセスするプログラム
2. **MCPクライアント**: サーバーとの1対1の接続を維持するプロトコルクライアント
3. **MCPサーバー**: 標準化されたModel Context Protocolを通じて特定の機能を公開する軽量プログラム
4. **ローカルデータソース**: MCPサーバーが安全にアクセスできるコンピューターのファイル、データベース、サービス
5. **リモートサービス**: MCPサーバーが接続できるAPIなどを通じて利用可能な外部システム

### 3.2 MCPサーバータイプ

MCPの仕様では、使用するトランスポートメカニズムに基づいて2種類のサーバーが定義されています：

1. **stdioサーバー**: アプリケーションのサブプロセスとして実行される「ローカル」サーバー
2. **HTTP over SSEサーバー**: URLを通じて接続する「リモート」サーバー

Agent SDKでは、`MCPServerStdio`と`MCPServerSse`クラスを使ってこれらのサーバーに接続できます。

### 3.3 MCPサーバーの実装方法

MCPサーバーの実装は比較的簡単です。以下に、Pythonを使用した独自のMCPサーバーの実装例を示します。

```python
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# FastMCPサーバーの初期化
mcp = FastMCP("weather")

# ツールの実装
@mcp.tool()
async def get_weather(city: str) -> str:
    """
    都市の天気情報を取得します。
    
    Args:
        city: 都市名（例: Tokyo, New York）
    """
    # ここで実際の天気APIを呼び出す実装を行う
    return f"{city}の天気は晴れです。気温は20度です。"

# サーバーの起動
if __name__ == "__main__":
    # stdioトランスポートを使用してサーバーを起動
    mcp.run(transport='stdio')
```

この例では、`FastMCP`クラスを使用して、簡単な天気情報を提供するMCPサーバーを実装しています。`@mcp.tool()`デコレータを使用して、LLMがアクセスできるツール（関数）を定義します。Pythonの型ヒントとドキュストリングは自動的にツール定義に変換されます。

### 3.4 OpenAI Agent SDKでのMCPサーバーの利用方法

OpenAI Agent SDKでMCPサーバーを使用する方法を以下に示します：

```python
import asyncio
import os
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerStdio

async def main():
    # MCPサーバーの設定（この例ではファイルシステムにアクセスするサーバー）
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_files")
    
    # MCPServerStdioを使用して、サブプロセスとしてMCPサーバーを起動
    async with MCPServerStdio(
        name="Filesystem Server",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
    ) as server:
        # エージェントの作成とMCPサーバーの統合
        agent = Agent(
            name="Assistant",
            instructions="Use the tools to read the filesystem and answer questions based on those files.",
            mcp_servers=[server],  # MCPサーバーをエージェントに接続
        )
        
        # エージェントの実行
        result = await Runner.run(agent, "Read the files and list them.")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

この例では、`MCPServerStdio`クラスを使用して、ファイルシステム用のMCPサーバーを起動し、それをエージェントに接続しています。エージェントはMCPサーバーを通じてファイルシステムにアクセスできるようになります。

重要なポイント：
1. `MCPServerStdio`はサーバーとの通信に標準入出力を使用します
2. `name`パラメータはサーバーを識別するための名前です
3. `params`にはサーバーを起動するためのコマンドと引数を指定します
4. エージェントの`mcp_servers`パラメータに、MCPサーバーのリストを渡します
5. エージェントが実行されるたびに、SDKはサーバーの`list_tools()`を呼び出してツール一覧を取得します
6. LLMがMCPツールを呼び出すと、SDKはサーバーの`call_tool()`を呼び出して処理を行います

### 3.5 MCPサーバーのキャッシング

エージェントが実行されるたびに`list_tools()`が呼び出されるため、特にリモートサーバーの場合は遅延が発生する可能性があります。ツールリストをキャッシュするには、以下のように`cache_tools_list=True`パラメータを指定します：

```python
async with MCPServerStdio(
    name="Filesystem Server",
    params={...},
    cache_tools_list=True  # ツールリストをキャッシュする
) as server:
    # ...
```

キャッシュを無効化するには、サーバーの`invalidate_tools_cache()`メソッドを呼び出します。

### 3.6 トレーシング

トレーシングは自動的にMCP操作をキャプチャします：
- MCPサーバーへのツールリスト取得呼び出し
- 関数呼び出しに関するMCP関連情報

## 4. まとめ

MCPプロトコルは、LLMとデータソース・ツールとの間の標準インターフェースを提供し、AIエージェントアプリケーションの開発を容易にします。OpenAI Agent SDKを使用することで、Claude 3.7 Sonnetを含む様々なLLMプロバイダーと統合できます。

MCPサーバーを実装することで、独自のデータソースやツールをLLMに提供することが可能です。これにより、LLMが特定のドメイン知識にアクセスしたり、独自のAPIと連携したりすることができます。

Agent SDKをMCPクライアントとして使用することで、既存のMCPサーバーとの連携が容易になり、エージェント間の効率的な通信と外部ツールとの連携を実現できます。

Planning Agentシステムの実装においては、これらの技術を活用して、各エージェント間の効率的な通信と、外部ツールとの連携を実現することが推奨されます。 