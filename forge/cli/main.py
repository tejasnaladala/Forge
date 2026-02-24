from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.version import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="forge")
def cli():
    """Forge -- universal AI agent runtime."""
    pass


@cli.command()
@click.argument("input_text", required=False)
@click.option("-a", "--agent", default=None, help="Agent name from the forgefile.")
@click.option("-m", "--model", default=None, help="Override the model (e.g., gpt-4o, ollama/llama3.2:3b).")
@click.option("-f", "--file", "forgefile", default="forgefile.yaml", help="Path to the forgefile.")
def run(input_text, agent, model, forgefile):
    """Execute an agent with the given prompt."""
    asyncio.run(_run_agent(input_text, agent, model, forgefile))


async def _run_agent(input_text, agent_name, model_override, forgefile):
    from forge.config import settings
    from forge.core.parser import ForgefileParser
    from forge.core.runtime import AgentRuntime
    from forge.core.types import AgentConfig, MemoryConfig, ModelConfig, StepType
    from forge.memory.manager import MemoryManager
    from forge.models.router import ModelRouter
    from forge.tools.executor import ToolExecutor
    from forge.tools.registry import ToolRegistry

    if not input_text:
        input_text = click.prompt("Enter your prompt")

    # Parse forgefile or use defaults
    config = None
    forgefile_path = Path(forgefile)
    if forgefile_path.is_file():
        parser = ForgefileParser()
        parsed = parser.parse_file(forgefile_path)
        agents = parsed.get("agents", {})
        if agent_name and agent_name in agents:
            config = agents[agent_name]
        elif agents:
            config = next(iter(agents.values()))

    if config is None:
        config = AgentConfig(
            name="default",
            model=ModelConfig(
                provider=settings.default_provider,
                model=settings.default_model,
            ),
            system_prompt="You are a helpful AI assistant. Be concise and helpful.",
            memory=MemoryConfig(),
        )

    if model_override:
        config.model = ForgefileParser._parse_model_shorthand(model_override)

    # Setup
    tool_registry = ToolRegistry()
    tool_registry.load_builtins()
    tool_executor = ToolExecutor(tool_registry)
    model_router = ModelRouter()
    memory_manager = MemoryManager(config.memory)

    runtime = AgentRuntime(
        config=config,
        model_router=model_router,
        tool_executor=tool_executor,
        memory_manager=memory_manager,
    )

    # Show info
    tools_list = ", ".join(tool_registry.list_tools())
    console.print(Panel(
        f"[bold]Agent:[/bold] {config.name}\n"
        f"[bold]Model:[/bold] {config.model.provider.value}/{config.model.model}\n"
        f"[bold]Tools:[/bold] {tools_list}",
        title="Forge",
        border_style="blue",
    ))

    # Run
    session = await runtime.create_session()
    console.print(f"\n[dim]Session: {session.id}[/dim]\n")

    gen = await runtime.run(session.id, input_text, stream=True)
    async for step in gen:
        if step.type == StepType.THINK:
            if step.output:
                console.print(f"[yellow]Think:[/yellow] {str(step.output)[:200]}")
        elif step.type == StepType.TOOL_CALL:
            tool_info = step.input or {}
            if step.error:
                console.print(f"[red]Tool Error ({tool_info.get('tool', '?')}):[/red] {step.error}")
            else:
                console.print(f"[cyan]Tool:[/cyan] {tool_info.get('tool', '?')}({tool_info.get('arguments', {})})")
                output_str = str(step.output or "")
                if len(output_str) > 300:
                    output_str = output_str[:300] + "..."
                console.print(f"[dim]{output_str}[/dim]")
        elif step.type == StepType.RESPOND:
            console.print(f"\n[green]{step.output}[/green]")

    # Summary
    console.print(f"\n[dim]Cost: ${session.total_cost:.4f} | Tokens: {session.total_tokens} | Steps: {len(session.steps)}[/dim]")


@cli.command()
@click.option("-f", "--file", "forgefile", default="forgefile.yaml", help="Path to the forgefile.")
@click.option("-p", "--port", default=8626, help="Port for the API server.")
def up(forgefile, port):
    """Start all agents from the forgefile and launch the API server."""
    asyncio.run(_start_server(forgefile, port))


async def _start_server(forgefile, port):
    import uvicorn
    from forge.api.app import create_app
    from forge.core.parser import ForgefileParser
    from forge.core.registry import AgentRegistry
    from forge.core.runtime import AgentRuntime
    from forge.memory.manager import MemoryManager
    from forge.models.router import ModelRouter
    from forge.orchestration.engine import OrchestrationEngine
    from forge.tools.executor import ToolExecutor
    from forge.tools.registry import ToolRegistry

    app = create_app()

    # Pre-initialize app state so agent registration works before lifespan
    tool_registry = ToolRegistry()
    tool_registry.load_builtins()
    model_router = ModelRouter()
    tool_executor = ToolExecutor(tool_registry)
    orchestration = OrchestrationEngine()
    agent_registry = AgentRegistry()

    app.state.model_router = model_router
    app.state.tool_registry = tool_registry
    app.state.tool_executor = tool_executor
    app.state.orchestration = orchestration
    app.state.agent_registry = agent_registry

    forgefile_path = Path(forgefile)
    if forgefile_path.is_file():
        parser = ForgefileParser()
        parsed = parser.parse_file(forgefile_path)

        for name, config in parsed.get("agents", {}).items():
            memory_manager = MemoryManager(config.memory)
            runtime = AgentRuntime(
                config=config,
                model_router=model_router,
                tool_executor=tool_executor,
                memory_manager=memory_manager,
            )
            orchestration.register_runtime(name, runtime)
            agent_registry.register(config)
            console.print(f"[green]Registered agent:[/green] {name}")

    console.print(Panel(
        f"Server starting on http://0.0.0.0:{port}\n"
        f"API docs at http://localhost:{port}/docs",
        title="Forge Server",
        border_style="green",
    ))

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


@cli.command()
def init():
    """Generate a default forgefile.yaml in the current directory."""
    template = """agent:
  name: my-agent
  model: claude-sonnet-4-20250514
  # model: ollama/llama3.2:3b  # Uncomment for free local model
  system_prompt: |
    You are a helpful AI assistant. You can search the web,
    fetch URLs, read/write files, and execute code.
    Be concise and helpful.
  tools:
    - web_search
    - web_fetch
    - file_ops
    - python_exec
  cost_limit: 5.0
  memory:
    backend: sqlite
"""
    path = Path("forgefile.yaml")
    if path.exists():
        console.print("[yellow]forgefile.yaml already exists. Skipping.[/yellow]")
        return

    path.write_text(template, encoding="utf-8")
    console.print("[green]Created forgefile.yaml[/green]")
    console.print("Edit it to configure your agent, then run: [bold]forge run[/bold]")


@cli.command()
def models():
    """List available models across all configured providers."""
    asyncio.run(_list_models())


async def _list_models():
    from forge.models.router import ModelRouter

    router = ModelRouter()
    available = await router.list_available_models()

    table = Table(title="Available Models")
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Type", style="yellow")

    for m in available:
        model_type = "Local" if m.get("local") else "Cloud"
        table.add_row(m["provider"], m["model"], model_type)

    console.print(table)

    if not available:
        console.print("[yellow]No models found. Set API keys in .env or start Ollama.[/yellow]")


@cli.command()
@click.option("-p", "--port", default=8626, help="Port for the API server.")
def server(port):
    """Start the REST API server."""
    asyncio.run(_start_server("forgefile.yaml", port))


if __name__ == "__main__":
    cli()
