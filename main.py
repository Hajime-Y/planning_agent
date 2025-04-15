# main.py
import asyncio
import logging
import os
import sys
from typing import List, Dict, Union

# from agents import Runner # Runner は front_agents で使用
# from agents.mcp import MCPServerStdio # MCPServerStdio は front_agents で使用
# from openai import AsyncOpenAI # openai は front_agents で使用（間接的に）
from dotenv import load_dotenv

# 新しく作成したエージェント実行関数をインポート
from front_agents.generic_task_agent import run_agent_session, DEFAULT_MODEL

# .envファイルから環境変数を読み込む
load_dotenv()

# ロガー設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MCPサーバーコマンド定義は front_agents に移動
# PLANNING_AGENT_SERVER_COMMAND = [sys.executable, "mcp_interface/server.py"]

async def main():
    """メイン処理: ユーザーとの対話ループを実行し、エージェントセッションを管理する"""
    logger.info("Starting the Front Agent Client...")

    # 環境変数からOpenAI APIキーを取得 (Agent SDK が内部で使用する可能性があるためチェック)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable not set. Agent SDK might require it.")
    else:
        logger.info("OPENAI_API_KEY found.")

    conversation_history: List[Dict] = [] # 会話履歴を保持するリスト
    current_input: Union[str, List[Dict]] = None # 現在のターンへの入力

    print("Welcome to the Agent Chat! Type 'quit' or 'exit' to end the session.")

    while True:
        try:
            # --- ユーザーからの入力を受け付け --- 
            if not conversation_history: # 最初のターン
                user_message = input("\nPlease enter the initial task or request: ")
                current_input = user_message # 初回は文字列
            else:
                user_message = input("\nUser: ")
                if user_message.lower() in ["quit", "exit"]:
                    print("Exiting chat session.")
                    break # ループを抜ける
                # 履歴にユーザーメッセージを追加して入力リストを作成
                current_input = conversation_history + [{"role": "user", "content": user_message}]

            if not user_message:
                continue # 空の入力は無視

            # --- エージェントセッションの実行 --- 
            print("Agent thinking...") # 応答待機中メッセージ
            result = await run_agent_session(
                user_input=current_input,
                # model="gpt-4o" # モデルを変更する場合
                # use_planning_server=False # Planning Server を使用しない場合
            )

            # --- 結果の表示 --- 
            if result and result.final_output:
                print(f"\nAgent: {result.final_output}")
                # 次のターンのために会話履歴を更新
                conversation_history = result.to_input_list()
            else:
                print("\nAgent session finished without a final output for this turn.")
                # エラーなどで final_output がない場合でも、履歴は更新しておく
                # (エラーメッセージ等が内部的に履歴に含まれている可能性があるため)
                if result:
                    conversation_history = result.to_input_list()
                # else の場合 (run_agent_session が例外を投げた場合) は履歴はそのまま

        except ConnectionRefusedError:
            logger.error("Failed to connect to the Planning Agent MCP Server. Is it running correctly?")
            print("\n[Error] Could not connect to the Planning Agent server. Please ensure it is running and restart the chat.")
            break # 接続エラー時はループ中断
        except FileNotFoundError:
             logger.error(f"Failed to start MCP Server. Script not found.")
             print("\n[Error] Could not find the MCP server script. Check installation and restart the chat.")
             break # サーバー起動失敗時もループ中断
        except Exception as e:
            logger.error(f"An unexpected error occurred during the turn: {e}", exc_info=True)
            print(f"\n[Error] An unexpected error occurred: {e}")
            # エラーが発生しても会話を続けられるように、break しない
            # 必要であれば、ここで conversation_history をリセットするなどの処理を追加

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nKeyboardInterrupt received. Exiting.")
