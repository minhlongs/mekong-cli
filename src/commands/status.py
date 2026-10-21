# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI Status Command - System health & API status
"""

import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.commands.status_helpers import run_health_check, run_quota_status

app = typer.Typer(name="status", help="System health & API status")
console = Console()


@app.command()
def system() -> None:
    """Show system health status"""
    from src.core.config import get_config
    from src.core.governance import Governance
    from src.core.memory_canonical import MemoryStore
    from src.providers.llm.client import get_client

    console.print(
        Panel(
            Text("🏥 Mekong System Health", style="bold cyan"),
            border_style="cyan",
        )
    )

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f"[bold]Python:[/bold] {python_version}")

    config = get_config()
    config_status = "✅" if config else "❌"
    console.print(f"[bold]Config:[/bold] {config_status}")

    llm_client = get_client()
    llm_status = "✅" if llm_client and llm_client.is_available else "❌"
    llm_model = llm_client.model if llm_client and llm_client.is_available else "N/A"
    console.print(f"[bold]LLM Client:[/bold] {llm_status} (Model: {llm_model})")

    try:
        memory = MemoryStore()
        stats = memory.stats()
        console.print(f"[bold]Memory:[/bold] ✅ ({stats['total']} executions)")
    except Exception:
        console.print("[bold]Memory:[/bold] ❌")

    try:
        gov = Governance()
        is_halted = gov.is_halted()
        status = "🔴 HALTED" if is_halted else "🟢 RUNNING"
        console.print(f"[bold]Governance:[/bold] {status}")
    except Exception:
        console.print("[bold]Governance:[/bold] ❌")


@app.command()
def api() -> None:
    """Check API provider status and quota"""
    from src.core.provider_registry import ProviderRegistry
    from src.providers.llm.client import get_client

    console.print(
        Panel(
            Text("🔌 API Provider Status", style="bold green"),
            border_style="green",
        )
    )

    llm_client = get_client()
    if not llm_client or not llm_client.is_available:
        console.print("[red]LLM Client not available[/red]")
        return

    console.print(f"[bold]Proxy URL:[/bold] {llm_client.proxy_url or 'N/A'}")
    console.print(f"[bold]Model:[/bold] {llm_client.model}")
    console.print(f"[bold]Mode:[/bold] {llm_client.mode}")
    console.print("[bold]Status:[/bold] [green]Connected[/green]")

    try:
        registry = ProviderRegistry()
        providers = registry.list_providers()

        table = Table(title="Registered Providers")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="green")

        for provider in providers:
            table.add_row(
                provider.name,
                provider.provider_type,
                "✅ Active" if provider.is_available else "❌ Inactive",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[dim]Provider details: {e}[/dim]")


@app.command()
def quota() -> None:
    """Show API quota and usage limits"""
    run_quota_status()


@app.command()
def health() -> None:
    """Full health check with recommendations"""
    run_health_check()


@app.command(name="all")
def status_all() -> None:
    """Show complete status (system + api + quota + health)"""
    system()
    console.print("\n")
    api()
    console.print("\n")
    quota()
    console.print("\n")
    health()


def main():
    """Entry point for status subcommands"""
    app()


if __name__ == "__main__":
    app()
