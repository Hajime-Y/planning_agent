import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
import json

# Import the CLI app object and the tool functions/agent creator
from cli import app, AVAILABLE_MCP_TOOLS
# We need to import the *module* for patching, not the function directly
import mcp_interface.server
import agents.planning_manager

runner = CliRunner()

# --- Tests for 'mcp call' command ---

@pytest.mark.parametrize(
    "tool_name, args_json, expected_args",
    [
        ("create_plan", '{"task_description": "test task"}', {"task_description": "test task"}),
        ("update_plan", '{"task_number": 1, "artifacts": ["a.txt"], "comments": "ok"}', {"task_number": 1, "artifacts": ["a.txt"], "comments": "ok"}),
        ("report_issue", '{"task_number": 2, "issue_description": "failed"}', {"task_number": 2, "issue_description": "failed"}),
        ("reset_plan", '{}', {}),
    ]
)
@patch.dict("cli.AVAILABLE_MCP_TOOLS", {
    "create_plan": MagicMock(return_value="plan created"),
    "update_plan": MagicMock(return_value="plan updated"),
    "report_issue": MagicMock(return_value="issue reported"),
    "reset_plan": MagicMock(return_value={"status": "success"}),
}, clear=True)
def test_mcp_call_success(tool_name, args_json, expected_args):
    """Test successful calls to MCP functions via CLI."""
    mock_func = AVAILABLE_MCP_TOOLS[tool_name]
    result = runner.invoke(app, ["mcp", "call", tool_name, args_json])

    assert result.exit_code == 0
    assert f"Calling MCP function: {tool_name}" in result.stdout
    assert f"Arguments: {expected_args}" in result.stdout
    assert "Result:" in result.stdout
    mock_func.assert_called_once_with(**expected_args)

def test_mcp_call_unknown_tool():
    """Test calling a non-existent MCP tool."""
    result = runner.invoke(app, ["mcp", "call", "nonexistent_tool", "{}"])
    assert result.exit_code == 1
    assert "Error: Unknown tool name: nonexistent_tool" in result.stdout
    assert "Available tools are:" in result.stdout

def test_mcp_call_invalid_json():
    """Test calling an MCP tool with invalid JSON arguments."""
    result = runner.invoke(app, ["mcp", "call", "create_plan", "{invalid json"]) # Malformed JSON
    assert result.exit_code == 1
    assert "Error: Invalid JSON format for arguments:" in result.stdout

def test_mcp_call_argument_mismatch():
    """Test calling an MCP tool with incorrect arguments (causing TypeError)."""
    # Patch the real function to simulate a TypeError if needed, or rely on the mock setup
    # Here, we pass args that the *real* create_plan would reject
    with patch.dict("cli.AVAILABLE_MCP_TOOLS", {"create_plan": mcp_interface.server.create_plan}, clear=True):
      result = runner.invoke(app, ["mcp", "call", "create_plan", '{"wrong_arg": 123}'])
      assert result.exit_code == 1
      assert "Error calling function create_plan: Argument mismatch" in result.stdout
      assert "Expected arguments for create_plan:" in result.stdout

# --- Tests for 'chat' command ---

# Patch LiteLLMModel directly within the planning_manager module
@patch('agents.planning_manager.LiteLLMModel')
def test_chat_mode_starts_and_runs_agent(mock_litellm_model):
    """Test that chat mode initializes the agent and calls its run method."""
    # Mock the agent instance returned by create_planning_manager_agent
    # Since we patched LiteLLMModel, create_planning_manager_agent *should* now run quickly,
    # but we still need to control the agent's behavior (run method)
    mock_agent_instance = MagicMock()
    mock_agent_instance.run.return_value = "Agent response"

    # Patch create_planning_manager_agent where it's looked up (in the cli module)
    with patch('cli.create_planning_manager_agent') as mock_create_agent:
        mock_create_agent.return_value = mock_agent_instance

        # Simulate user typing 'hello' and then 'quit'
        result = runner.invoke(app, ["chat"], input="hello\nquit\n")

        assert result.exit_code == 0
        mock_create_agent.assert_called_once()
        # mock_litellm_model.assert_called_once() # Verify LiteLLMModel was 'initialized' (mocked)
        assert "Initializing Planning Agent..." in result.stdout
        assert "Agent initialized. Entering chat mode..." in result.stdout
        assert "Agent thinking..." in result.stdout
        mock_agent_instance.run.assert_called_once_with("hello")
        assert "Agent: Agent response" in result.stdout
        assert "Exiting chat mode." in result.stdout

# Patch LiteLLMModel to simulate initialization error
@patch('agents.planning_manager.LiteLLMModel')
def test_chat_mode_agent_initialization_error(mock_litellm_model):
    """Test handling of errors during agent initialization (mocked LiteLLMModel)."""
    # Simulate error during LiteLLMModel initialization inside create_planning_manager_agent
    mock_litellm_model.side_effect = Exception("Simulated LiteLLM Init failed")

    result = runner.invoke(app, ["chat"])

    assert result.exit_code == 1
    assert "Initializing Planning Agent..." in result.stdout # It starts initialization
    # Check for the error message originating from the *create_planning_manager_agent* try/except block
    # or the top-level exception handler in cli.py if it propagates
    assert "Error initializing agent: Simulated LiteLLM Init failed" in result.stdout

# Patch LiteLLMModel and the run method
@patch('agents.planning_manager.LiteLLMModel')
def test_chat_mode_agent_run_error(mock_litellm_model):
    """Test handling of errors during agent execution (run method)."""
    # Mock the agent instance and its run method behavior
    mock_agent_instance = MagicMock()
    mock_agent_instance.run.side_effect = Exception("Runtime error")

    # Patch create_planning_manager_agent where it's looked up (in the cli module)
    with patch('cli.create_planning_manager_agent') as mock_create_agent:
        mock_create_agent.return_value = mock_agent_instance

        # Simulate user typing 'test' and then 'quit'
        result = runner.invoke(app, ["chat"], input="test\nquit\n")

        assert result.exit_code == 0 # Chat mode continues after error in this setup
        mock_create_agent.assert_called_once()
        mock_agent_instance.run.assert_called_once_with("test")
        assert "Error during agent execution: Runtime error" in result.stdout
        assert "Exiting chat mode." in result.stdout # Ensure it still exits correctly 