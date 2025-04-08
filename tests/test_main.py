# tests/test_main.py
import asyncio
# import signal # 不要なので削除
import sys
from unittest.mock import patch, AsyncMock, MagicMock
import logging

import pytest
from pytest_mock import MockerFixture  # pytest-mock の型ヒント用

# テスト対象のモジュールをインポート
# main.py はプロジェクトルートにあるため、パス調整が必要な場合がある
# pytest実行時のカレントディレクトリがプロジェクトルートなら通常不要
import main

# pytest-asyncio が必要: `uv add pytest-asyncio`
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_mcp_server_stdio(mocker: MockerFixture):
    """MCPServerStdio をモックするフィクスチャ"""
    mock_server_instance = AsyncMock()
    mock_server_instance.list_tools.return_value = [
        {"name": "create_plan", "description": "...", "parameters": {}},
        {"name": "update_plan", "description": "...", "parameters": {}},
        # 必要に応じて他のツールもモック
    ]
    # __aenter__ と __aexit__ をモック
    mock_server_constructor = mocker.patch('main.MCPServerStdio', return_value=mock_server_instance)
    # コンテキストマネージャとして使えるようにする
    mock_server_instance.__aenter__.return_value = mock_server_instance
    mock_server_instance.__aexit__.return_value = None
    return mock_server_constructor, mock_server_instance

@pytest.fixture
def mock_agent_runner(mocker: MockerFixture):
    """agents.Runner.run をモックするフィクスチャ"""
    mock_run = mocker.patch('main.Runner.run', new_callable=AsyncMock)
    mock_result = MagicMock()
    mock_result.final_output = "Mocked agent output"
    mock_run.return_value = mock_result
    return mock_run

@pytest.fixture
def mock_input(mocker: MockerFixture):
    """input() 関数をモックするフィクスチャ"""
    return mocker.patch('builtins.input', return_value="test task description")

@pytest.fixture
def mock_signal_handler(mocker: MockerFixture):
    # このフィクスチャは shutdown テスト以外でも使われている可能性があるため残す
    # (test_main_successful_run で利用)
    return mocker.patch('asyncio.AbstractEventLoop.add_signal_handler')

async def test_main_successful_run(
    mock_mcp_server_stdio, mock_agent_runner, mock_input, mock_signal_handler, 
    mocker: MockerFixture, # 引数に mocker を追加
    caplog # event_loop を削除
):
    """main 関数が正常に実行され、Agent が呼び出されるかのテスト"""
    mock_constructor, mock_server = mock_mcp_server_stdio
    # main.shutdown_requested は削除されたので不要
    # main.shutdown_requested = False
    
    # ロガーレベルを設定してキャプチャを確実にする
    caplog.set_level(logging.INFO, logger='main') 

    # main() を実行するためのタスクを作成 (asyncio.create_task を使用)
    main_task = asyncio.create_task(main.main())

    # 少し待機して main() 内の処理が進むようにする
    await asyncio.sleep(0.3) # 待機時間

    # アサーション
    mock_constructor.assert_called_once() # MCPServerStdioが呼ばれたか
    mock_constructor.assert_called_with(
        name='PlanningAgentServer', 
        params={'command': sys.executable, 'args': ['mcp_interface/server.py']}, 
        cache_tools_list=True
    )
    mock_server.list_tools.assert_awaited_once() # list_tools が呼ばれたか
    mock_input.assert_called_once() # input() が呼ばれたか
    # mocker.ANY を使って Agent インスタンスをチェック (mocker が引数に追加されたので OK)
    mock_agent_runner.assert_awaited_once_with(mocker.ANY, "test task description") 
    
    # Runner.run が完了し、ログが出力されるまで待機
    await asyncio.sleep(0.1) # 追加の短い待機
    
    # assert mock_signal_handler.call_count == 2 # シグナルハンドラは削除したのでコメントアウト済みのまま
    assert "Agent run finished." in caplog.text # ログ出力の確認

    # テスト完了後にタスクをキャンセルしてクリーンアップ
    if not main_task.done():
        main_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await main_task
    else:
        # タスクが既に完了している場合、例外が発生していないか確認
        exc = main_task.exception()
        if exc:
            pytest.fail(f"Main task completed with an unexpected exception: {exc}")
        # 正常完了なら result() は None (main() が return しないため)
        assert main_task.result() is None

async def test_main_mcp_connection_error(
    mocker: MockerFixture, 
    caplog # event_loop を削除
):
    """MCPサーバー接続失敗時のエラーハンドリングテスト"""
    # MCPServerStdio の __aenter__ で例外を発生させるようにモック
    mock_server_instance = AsyncMock()
    mock_server_instance.__aenter__.side_effect = ConnectionRefusedError("Connection failed")
    mock_constructor = mocker.patch('main.MCPServerStdio', return_value=mock_server_instance)
    mocker.patch('asyncio.AbstractEventLoop.add_signal_handler') # シグナルハンドラはモック（ただし main.py からは削除済）
    # main.shutdown_requested は削除されたので不要
    # main.shutdown_requested = False

    # main() を実行 (asyncio.create_task を使用)
    main_task = asyncio.create_task(main.main())

    # main() が完了するのを待つ (エラーで終了するはず)
    await asyncio.sleep(0.2) 

    # アサーション
    assert "Failed to connect to the Planning Agent MCP Server" in caplog.text
    assert mock_constructor.called # コンストラクタは呼ばれる
    mock_server_instance.__aenter__.assert_awaited_once() # __aenter__ が呼ばれてエラー発生

    # mainタスクが完了しているはず (エラーログ出力後、正常終了)
    assert main_task.done()
    # --- pytest.raises ブロックを削除 --- 
    # with pytest.raises(ConnectionRefusedError):
    #     pass # ログで確認済みのためここでは何もしない
    # キャンセルされていないことを確認
    assert not main_task.cancelled()


async def test_main_mcp_command_not_found(
    mocker: MockerFixture, 
    caplog # event_loop を削除
):
    """MCPサーバー起動コマンドが見つからない場合のエラーハンドリング"""
    mock_server_instance = AsyncMock()
    expected_error = FileNotFoundError(f"Command not found: {main.PLANNING_AGENT_SERVER_COMMAND[0]}")
    mock_server_instance.__aenter__.side_effect = expected_error
    mock_constructor = mocker.patch('main.MCPServerStdio', return_value=mock_server_instance)
    mocker.patch('asyncio.AbstractEventLoop.add_signal_handler')
    # main.shutdown_requested は削除されたので不要
    # main.shutdown_requested = False

    # main() を実行 (asyncio.create_task を使用)
    main_task = asyncio.create_task(main.main())
    await asyncio.sleep(0.2) # エラー処理完了待ち

    assert f"Failed to start MCP Server. Command not found: {' '.join(main.PLANNING_AGENT_SERVER_COMMAND)}" in caplog.text
    assert main_task.done()
    assert not main_task.cancelled()
    # main関数内でエラーがキャッチされログ出力されるため、タスク自体は正常終了する
    # 例外が再スローされる場合は以下のアサーションが有効
    # with pytest.raises(FileNotFoundError):
    #     main_task.result()


# --- main() 以外のヘルパー関数等のテストも必要であれば追加 ---

# --- test_shutdown_invokes_cancel_and_stop_synchronously_as_possible 関数全体を削除 ---
# def test_shutdown_invokes_cancel_and_stop_synchronously_as_possible(...): ... 