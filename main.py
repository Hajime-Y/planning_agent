# main.py
import asyncio
import logging
import os
import sys
from typing import List

from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

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

    # 環境変数からOpenAI APIキーを取得
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set. Please set it before running.")
        return # APIキーがない場合は終了
    logger.info("OPENAI_API_KEY found.") # キーが見つかったことをログに出力

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
            # エージェントの名前と指示を変更
            agent = Agent(
                name="GenericTaskAgent", # 名前変更
                instructions=(
                    "You are an agent designed to accomplish tasks. "
                    "Then, you MUST use the 'create_plan' tool provided by the PlanningAgentServer "
                    "to get a step-by-step plan or clarifying questions for the new task. The user will provide an initial request. "
                    "Use the available tools based on the plan. Report progress or issues using 'update_plan' or 'report_issue' when appropriate."
                ),
                mcp_servers=[planning_server], # MCPサーバーをエージェントに接続
                # model= # 必要であればモデルを指定 (デフォルトはOpenAIのモデルになる可能性)
                # openai_client= # カスタムクライアントを使用する場合
            )
            logger.info("Generic Task Agent initialized.") # ログも更新

            # --- ここからAgentの実行ロジック ---
            initial_user_request = input("Please enter the initial task or request: ")

            # 初期リクエストをそのまま渡すのではなく、計画作成を促すプロンプトを作成
            planning_prompt = (
                f"Based on the following user request, first use the 'create_plan' tool to create a plan or ask clarifying questions. "
                f"User request: '{initial_user_request}'"
            )

            logger.info(f"Running agent with planning prompt: '{planning_prompt}'")
            try:
                # 修正したプロンプトで Agent を実行
                result = await Runner.run(agent, planning_prompt)
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
