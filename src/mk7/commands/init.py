"""Mekong CLI 7 — init command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ..core.config import initialize, load
from ..core.llm import LLMClient
from ..core.models import all_models

console = Console()


def init_cmd(
    base_url: str | None = typer.Option(None, "--base-url", help="OmniRoute gateway URL"),
    token: str | None = typer.Option(None, "--token", help="OmniRoute API token"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Initialize Mekong CLI 7 config."""
    config = initialize(base_url=base_url, token=token)
    console.print(f"[bold green]✔[/] config written to ~/.mekong/config.json")
    console.print(f"  base_url : [cyan]{config['base_url']}[/]")
    console.print(f"  model    : [cyan]{config['default_model']}[/]")

    console.print("\n[bold]Testing gateway...[/]")
    client = LLMClient()
    ok, detail = client.ping(config["default_model"])
    if ok:
        console.print(f"[bold green]✔[/] gateway reachable — {detail}")
    else:
        console.print(f"[bold red]✘[/] gateway FAIL — {detail}")
        raise typer.Exit(1)

    table = Table(title="Models")
    table.add_column("Model")
    table.add_column("Status")
    for m in all_models():
        ok, _ = client.ping(m.id)
        table.add_row(m.id, "[green]OK[/]" if ok else "[red]FAIL[/]")
    console.print(table)
