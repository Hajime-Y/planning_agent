import logging
import sys
import os
import asyncio
from typing import Optional, List, Union, Dict
import uuid

from agents import Agent, Runner, RunResult
from agents.mcp import MCPServerStdio

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4.1"

# Define the server command here
PLANNING_AGENT_SERVER_COMMAND = [sys.executable, "mcp_interface/server.py"]

def create_generic_task_agent(
    model: str = DEFAULT_MODEL,
    use_planning_server: bool = True,
    planning_server: Optional[MCPServerStdio] = None,
) -> Agent:
    """
    Creates and configures the Generic Task Agent.

    Args:
        model: The OpenAI model to use (e.g., "gpt-4.1").
        use_planning_server: Whether to connect the agent to the Planning Agent MCP server.
        planning_server: An existing MCPServerStdio instance if use_planning_server is True.

    Returns:
        An initialized Agent instance.

    Raises:
        ValueError: If use_planning_server is True but planning_server is not provided.
    """
    if use_planning_server and planning_server is None:
        raise ValueError("planning_server must be provided when use_planning_server is True")

    mcp_servers: List[MCPServerStdio] = [planning_server] if use_planning_server and planning_server else []

    # Base instructions
    instructions = "You are an agent designed to accomplish tasks based on user requests. Once given a task, you should autonomously complete it from start to finish without requiring additional prompting unless absolutely necessary for clarification. Take initiative and see tasks through to their logical conclusion."

    if use_planning_server:
        # Instructions when using the planning server
        instructions += (
            "1. When you receive a task request from the user, you MUST first use the 'create_plan' tool provided by the PlanningAgentServer to break down the task into a step-by-step plan or ask clarifying questions if needed. "
            "2. Once you have the plan, you MUST execute the steps in the plan sequentially using the available tools. "
            "3. After completing each step in the plan, you MUST use the 'update_plan' tool to report the completion of that step and the current overall progress. "
            "4. If you encounter an issue or get stuck during the execution of a step, use the 'report_issue' tool to report the specific problem encountered for that step. "
            "5. After successfully completing all steps in the plan, provide the final result or summary to the user."
        )
    else:
        # Simplified instructions when not using the planning server
         instructions += "Execute the user's request directly using the available tools."

    agent = Agent(
        name="GenericTaskAgent",
        instructions=instructions,
        mcp_servers=mcp_servers, # Pass the conditional list of servers
        model=model,
    )
    logger.info(f"Generic Task Agent initialized (Model: {model}, Planning Server: {'Enabled' if use_planning_server else 'Disabled'}).")
    return agent


async def run_agent_session(
    user_input: Union[str, List[Dict]],
    model: str = DEFAULT_MODEL,
    use_planning_server: bool = True,
    session_id: Optional[str] = None,
    base_data_dir: str = "./data"
) -> RunResult:
    """
    Sets up the planning server (if enabled), creates the agent, and runs a single turn.

    Args:
        user_input: The user's input for this turn (string or list of message dicts).
        model: The OpenAI model to use.
        use_planning_server: Whether to connect to and use the Planning Agent MCP server.
        session_id: Unique identifier for the session. If None, a new UUID is generated.
        base_data_dir: The base directory for storing session data.

    Returns:
        The RunResult object containing details of the agent run for this turn.

    Raises:
        ConnectionRefusedError: If connection to the MCP server fails.
        FileNotFoundError: If the MCP server script cannot be found.
        Exception: For other potential errors during server connection or agent execution.
    """
    if use_planning_server:
        current_session_id = session_id or str(uuid.uuid4())
        logger.info(f"Using session ID: {current_session_id}")

        session_data_dir = os.path.join(base_data_dir, "sessions", current_session_id)
        try:
            os.makedirs(session_data_dir, exist_ok=True)
            logger.info(f"Ensured session data directory exists: {session_data_dir}")
        except OSError as e:
            logger.error(f"Failed to create session directory '{session_data_dir}': {e}", exc_info=True)
            raise

        server_command_with_data_dir = PLANNING_AGENT_SERVER_COMMAND + ["--data-dir", session_data_dir]
        logger.info(f"Planning Agent Server command: {server_command_with_data_dir}")

        planning_server_config = {
            "name": "PlanningAgentServer",
            "params": {
                "command": server_command_with_data_dir[0],
                "args": server_command_with_data_dir[1:],
            },
            "cache_tools_list": True,
        }
        try:
            async with MCPServerStdio(**planning_server_config) as planning_server:
                logger.info("Successfully connected to Planning Agent MCP Server.")
                try:
                    tools_list = await planning_server.list_tools()
                    logger.info(f"Available tools from Planning Agent Server: {tools_list}")
                except Exception as e:
                    logger.error(f"Failed to list tools from MCP server: {e}", exc_info=True)
                    raise ConnectionError(f"Failed to communicate with MCP server: {e}") from e

                agent = create_generic_task_agent(
                    model=model,
                    use_planning_server=True,
                    planning_server=planning_server
                )
                logger.info(f"Running agent turn...")
                result = await Runner.run(agent, user_input)
                logger.info("Agent turn finished.")
                return result

        except (ConnectionRefusedError, FileNotFoundError) as e:
            logger.error(f"Failed to setup or connect to MCP Server: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during agent session with planning server: {e}", exc_info=True)
            raise

    else: # Not using planning server
        try:
            agent = create_generic_task_agent(model=model, use_planning_server=False)
            logger.info(f"Running agent turn (no planning server)...")
            result = await Runner.run(agent, user_input)
            logger.info("Agent turn finished.")
            return result
        except Exception as e:
            logger.error(f"Error during agent session without planning server: {e}", exc_info=True)
            raise 