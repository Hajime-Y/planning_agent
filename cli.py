import typer
import json # JSON parsing
from rich.console import Console
from rich.table import Table

# Import MCP tool functions directly
from mcp_interface.server import create_plan, update_plan, report_issue
# Import the agent creation function
from planning_agents.planning_manager import create_planning_manager_agent

# Store available tools in a dictionary for easy lookup
AVAILABLE_MCP_TOOLS = {
    "create_plan": create_plan,
    "update_plan": update_plan,
    "report_issue": report_issue,
}

# agentsモジュールや他のインポートは後で追加

app = typer.Typer(
    name="planning-agent-cli",
    help="Planning Agentのコマンドラインインターフェース",
    add_completion=False,
)
mcp_app = typer.Typer(help="MCPツールを直接呼び出します。")
app.add_typer(mcp_app, name="mcp")

console = Console()

# --- グローバルオプション (MCP URL removed) ---
@app.callback()
def main_options():
    """Planning Agent CLI"""
    pass


# --- MCPサブコマンド (Direct function call) ---
@mcp_app.command("call", help="指定されたMCPツール関数を直接呼び出します。引数は JSON 文字列で渡します。")
def mcp_call(
    tool_name: str = typer.Argument(..., help="呼び出すMCPツールの名前 (" + ", ".join(AVAILABLE_MCP_TOOLS.keys()) + ")"),
    args_json: str = typer.Argument('{"dummy_arg": "dummy_value"}', help="ツールに渡す引数 (JSON形式)"),
):
    """MCPツール関数を直接呼び出す"""
    console.print(f"[bold blue]Calling MCP function:[/bold blue] {tool_name}")

    # Find the function
    if tool_name not in AVAILABLE_MCP_TOOLS:
        console.print(f"[bold red]Error:[/bold red] Unknown tool name: {tool_name}")
        console.print(f"Available tools are: {', '.join(AVAILABLE_MCP_TOOLS.keys())}")
        raise typer.Exit(code=1)

    tool_func = AVAILABLE_MCP_TOOLS[tool_name]

    # Parse arguments
    try:
        args_dict = json.loads(args_json)
        console.print(f"[bold blue]Arguments:[/bold blue] {args_dict}")
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON format for arguments: {e}")
        raise typer.Exit(code=1)

    # Call the function
    try:
        result = tool_func(**args_dict)
        console.print("[bold green]Result:[/bold green]")
        # Pretty print the result (especially if it's a dict or list)
        if isinstance(result, (dict, list)):
            console.print_json(data=result)
        else:
            console.print(result)
    except TypeError as e:
        console.print(f"[bold red]Error calling function {tool_name}:[/bold red] Argument mismatch or incorrect arguments provided. {e}")
        import inspect
        sig = inspect.signature(tool_func)
        console.print(f"Expected arguments for {tool_name}: {sig}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error during function execution {tool_name}:[/bold red] {e}")
        # Optionally log the full traceback here
        raise typer.Exit(code=1)


# --- Chatサブコマンド ---
@app.command("chat", help="Planning Agentと対話モードで会話します。")
def chat_mode(
    # chatモード固有のオプションがあればここに追加
):
    """Planning Agentとの対話モードを開始する"""
    console.print("[bold green]Initializing Planning Agent...[/bold green]")
    try:
        # Create the agent instance
        agent = create_planning_manager_agent()
        console.print("[bold green]Agent initialized. Entering chat mode...[/bold green]")
        console.print("Type 'quit' or 'exit' to end the session.")
    except Exception as e:
        console.print(f"[bold red]Error initializing agent:[/bold red] {e}")
        raise typer.Exit(code=1)

    while True:
        user_input = typer.prompt(">")
        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("[bold red]Exiting chat mode.[/bold red]")
            break

        # Run the agent with user input
        try:
            console.print("[yellow]Agent thinking...[/yellow]") # Indicate activity
            response = agent.run(user_input)
            console.print(f"[cyan]Agent:[/cyan] {response}")
        except Exception as e:
            console.print(f"[bold red]Error during agent execution:[/bold red] {e}")
            # Optionally add more detailed error handling or logging
            # Continue the loop or exit based on the error severity?
            # For now, just print the error and continue
            pass


if __name__ == "__main__":
    app()
