# main.py
import asyncio
import logging
import os
import sys
from typing import List

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MCPサーバー (planning_agent) を起動するコマンド
# mcp_interface/server.py を実行する
# Pythonのパスを考慮する必要がある場合がある
PLANNING_AGENT_SERVER_COMMAND = [sys.executable, "mcp_interface/server.py"]

async def main():
    """メイン処理"""
    loop = asyncio.get_running_loop()

    logger.info("Starting the Planning Agent Client...")

    # 環境変数からOpenAI APIキーを取得 (Agent SDKが内部で使用する可能性がある)
    # 必要に応じて他の設定もここで行う (例: モデル名、カスタムクライアント)
    # api_key = os.getenv("OPENAI_API_KEY")
    # if not api_key:
    #     logger.error("OPENAI_API_KEY environment variable not set.")
    #     return # またはデフォルトキーを使用するか、エラー処理

    # MCPサーバー (planning_agent) への接続設定
    planning_server_config = {
        "name": "PlanningAgentServer",
        "params": {
            "command": PLANNING_AGENT_SERVER_COMMAND[0], # python実行可能ファイル
            "args": PLANNING_AGENT_SERVER_COMMAND[1:],  # server.pyスクリプト
        },
        "cache_tools_list": True, # ツールリストをキャッシュする
    }

    try:
        # MCPServerStdio を非同期コンテキストマネージャとして使用
        async with MCPServerStdio(**planning_server_config) as planning_server:
            logger.info("Successfully connected to Planning Agent MCP Server.")
            # 利用可能なツールリストを取得してログに出力（デバッグ用）
            try:
                tools_list = await planning_server.list_tools()
                logger.info(f"Available tools from Planning Agent Server: {tools_list}")
            except Exception as e:
                logger.error(f"Failed to list tools from MCP server: {e}", exc_info=True)
                # ツールリスト取得に失敗した場合でも処理を続けるか、エラーとするか要検討
                return

            # OpenAI Agent SDK を使用して Agent を初期化
            # ここでは基本的な設定のみ。必要に応じてモデルや指示を調整
            agent = Agent(
                name="PlanningCoordinatorAgent",
                instructions=(
                    "You are a coordinator agent. Use the available tools from the Planning Agent Server "
                    "to manage planning tasks based on user requests. Start by asking the user what task "
                    "they want to perform."
                ),
                mcp_servers=[planning_server], # MCPサーバーをエージェントに接続
                # model= # 必要であればモデルを指定 (デフォルトはOpenAIのモデルになる可能性)
                # openai_client= # カスタムクライアントを使用する場合
            )

            logger.info("Planning Coordinator Agent initialized.")

            # --- ここからAgentの実行ロジック ---
            # 例: ユーザーからの最初の指示を受け取り、Agentを実行
            # この部分は実際のユースケースに合わせて実装する必要がある
            initial_user_request = input("Please enter the initial task or request: ")

            logger.info(f"Running agent with initial request: '{initial_user_request}'")
            try:
                result = await Runner.run(agent, initial_user_request)
                logger.info("Agent run finished.")
                print("\n--- Agent Final Output ---")
                print(result.final_output)
                print("--------------------------\n")
            except Exception as e:
                logger.error(f"Error during agent execution: {e}", exc_info=True)
                print(f"\n[Error] Agent execution failed: {e}\n")

            # --- Agent実行ロジックここまで ---

    except asyncio.CancelledError:
        logger.info("Main task was cancelled.")
    except ConnectionRefusedError:
        logger.error("Failed to connect to the Planning Agent MCP Server. Is it running correctly?")
    except FileNotFoundError:
         logger.error(f"Failed to start MCP Server. Command not found: {' '.join(PLANNING_AGENT_SERVER_COMMAND)}")
         logger.error("Please ensure Python path and script path are correct.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    # 非同期イベントループを開始
    try:
        # main() を直接実行する形に変更 (main_task グローバル変数を削除したため)
        asyncio.run(main()) # asyncio.run で実行し、完了を待つ
    except KeyboardInterrupt:
        # KeyboardInterrupt時の処理も簡略化 (単純なログ出力のみ)
        logger.info("\nKeyboardInterrupt received. Exiting.")
