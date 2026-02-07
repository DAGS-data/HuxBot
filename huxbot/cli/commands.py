"""CLI commands for HuxBot."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import typer
from rich.console import Console

from huxbot import __version__

app = typer.Typer(
    name="huxbot",
    help="HuxBot – AI agent framework powered by Google ADK and LiteLLM",
    no_args_is_help=True,
)
console = Console()


def _version_cb(value: bool) -> None:
    if value:
        console.print(f"huxbot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(None, "--version", "-v", callback=_version_cb, is_eager=True),
) -> None:
    """HuxBot – Personal AI Agent."""


# ---------------------------------------------------------------------------
# onboard
# ---------------------------------------------------------------------------

@app.command()
def onboard() -> None:
    """Initialize HuxBot configuration and workspace."""
    from huxbot.config.loader import save_config, CONFIG_FILE
    from huxbot.config.schema import HuxBotConfig

    if CONFIG_FILE.exists():
        console.print(f"[yellow]Config already exists at {CONFIG_FILE}[/yellow]")
        if not typer.confirm("Overwrite?"):
            raise typer.Exit()

    config = HuxBotConfig()
    workspace = Path(config.agent.workspace).expanduser().resolve()
    save_config(config)
    console.print(f"[green]✓[/green] Created config at {CONFIG_FILE}")

    _create_workspace_templates(workspace)

    console.print("\nhuxbot is ready!")
    console.print("\nNext steps:")
    console.print("  1. Add your API key to [cyan]~/.huxbot/config.json[/cyan]")
    console.print("  2. Chat: [cyan]huxbot agent -m 'Hello!'[/cyan]")


def _create_workspace_templates(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    templates = {
        "AGENTS.md": (
            "# HuxBot Agent Configuration\n\n"
            "This file shapes how HuxBot responds through Google ADK.\n\n"
            "## Directives\n\n"
            "- Ground every answer in facts; say \"I don't know\" when uncertain\n"
            "- Keep replies under three paragraphs unless the user asks for depth\n"
            "- When a task involves multiple steps, outline them first\n"
            "- Persist key decisions and user preferences to memory/\n"
        ),
        "SOUL.md": (
            "# HuxBot Identity\n\n"
            "HuxBot is an ADK-powered personal agent that bridges chat\n"
            "platforms to large language models via LiteLLM.\n\n"
            "## Traits\n\n"
            "- Direct and low-ceremony — skip filler phrases\n"
            "- Opinionated when asked, neutral by default\n"
            "- Proactively surfaces related context from memory\n\n"
            "## Principles\n\n"
            "- Never fabricate sources or data\n"
            "- Respect rate limits and cost budgets\n"
            "- Protect user credentials — never echo secrets\n"
        ),
    }
    for filename, body in templates.items():
        fp = workspace / filename
        if not fp.exists():
            fp.write_text(body)
            console.print(f"  [dim]Created {filename}[/dim]")

    memory_dir = workspace / "memory"
    memory_dir.mkdir(exist_ok=True)
    mem_file = memory_dir / "MEMORY.md"
    if not mem_file.exists():
        mem_file.write_text(
            "# HuxBot Memory\n\n"
            "Persistent notes that carry across conversations.\n"
            "Add facts, preferences, and project context below.\n"
        )
        console.print("  [dim]Created memory/MEMORY.md[/dim]")


# ---------------------------------------------------------------------------
# agent
# ---------------------------------------------------------------------------

@app.command()
def agent(
    message: str = typer.Option(None, "--message", "-m", help="Single message to send"),
    session_id: str = typer.Option("cli:default", "--session", "-s", help="Session ID"),
) -> None:
    """Interact with the agent (interactive or single-message mode)."""
    from huxbot.config import load_config
    from huxbot.bus.queue import MessageBus
    from huxbot.agent.factory import build_agent_and_runner
    from huxbot.agent.processor import MessageProcessor

    config = load_config()
    if not config.provider.api_key:
        console.print("[red]Error: No API key configured.[/red]")
        console.print("Set it in ~/.huxbot/config.json → provider.api_key")
        raise typer.Exit(1)

    bus = MessageBus()
    _agent, runner, session_service = build_agent_and_runner(config, bus)
    processor = MessageProcessor(runner, session_service, bus)

    if message:
        async def _run_once() -> None:
            resp = await processor.process_single(message, session_id)
            console.print(f"\n{resp or '(no response)'}")

        asyncio.run(_run_once())
    else:
        console.print("HuxBot interactive mode (Ctrl+C to exit)\n")

        async def _run_interactive() -> None:
            while True:
                try:
                    user_input = console.input("[bold blue]You:[/bold blue] ")
                    if not user_input.strip():
                        continue
                    resp = await processor.process_single(user_input, session_id)
                    console.print(f"\n{resp or '(no response)'}\n")
                except (KeyboardInterrupt, EOFError):
                    console.print("\nGoodbye!")
                    break

        asyncio.run(_run_interactive())


# ---------------------------------------------------------------------------
# gateway
# ---------------------------------------------------------------------------

@app.command()
def gateway() -> None:
    """Start the HuxBot gateway (message bus + channels)."""
    from huxbot.config import load_config
    from huxbot.bus.queue import MessageBus
    from huxbot.agent.factory import build_agent_and_runner
    from huxbot.agent.processor import MessageProcessor
    from huxbot.channels.manager import ChannelManager

    config = load_config()
    if not config.provider.api_key:
        console.print("[red]Error: No API key configured.[/red]")
        raise typer.Exit(1)

    bus = MessageBus()
    _agent, runner, session_service = build_agent_and_runner(config, bus)
    processor = MessageProcessor(runner, session_service, bus)
    channels = ChannelManager(config, bus)

    if channels.enabled_channels:
        console.print(f"[green]✓[/green] Channels: {', '.join(channels.enabled_channels)}")
    else:
        console.print("[yellow]Warning: No channels enabled[/yellow]")

    console.print("Starting gateway...")

    async def _run() -> None:
        try:
            await asyncio.gather(
                processor.run(),
                channels.start_all(),
            )
        except KeyboardInterrupt:
            console.print("\nShutting down...")
            processor.stop()
            await channels.stop_all()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# chat
# ---------------------------------------------------------------------------

@app.command()
def chat(
    port: int = typer.Option(8501, "--port", "-p", help="Port for the Streamlit server"),
) -> None:
    """Open the HuxBot chat UI in the browser."""
    app_path = str(Path(__file__).parent.parent / "ui" / "app.py")
    subprocess.run(["streamlit", "run", app_path, "--server.port", str(port)])


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@app.command()
def status() -> None:
    """Show HuxBot configuration status."""
    from huxbot.config import load_config
    from huxbot.config.loader import CONFIG_FILE

    config = load_config()
    workspace = Path(config.agent.workspace).expanduser().resolve()

    console.print("HuxBot Status\n")
    console.print(
        f"Config: {CONFIG_FILE} {'[green]✓[/green]' if CONFIG_FILE.exists() else '[red]✗[/red]'}"
    )
    console.print(
        f"Workspace: {workspace} {'[green]✓[/green]' if workspace.exists() else '[red]✗[/red]'}"
    )
    console.print(f"Model: {config.agent.model}")
    console.print(
        f"API Key: {'[green]✓ set[/green]' if config.provider.api_key else '[dim]not set[/dim]'}"
    )

    for name in ("telegram", "discord", "whatsapp"):
        ch = getattr(config.channels, name)
        enabled = "[green]✓[/green]" if ch.enabled else "[dim]✗[/dim]"
        console.print(f"{name.capitalize()}: {enabled}")
