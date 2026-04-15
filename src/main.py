"""
Mekong CLI - Main Entry Point

RaaS Agency Operating System CLI.
Thin entry point only — all command logic lives in src/cli/.
App wiring happens in src/cli/app_setup.py.
"""

import os
import sys

# Allow running as script: python3 src/main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.cli.app_setup import build_app

console = Console()

# Fully wired app instance (sub-apps + all command groups)
app = build_app()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Mekong CLI: RaaS Agency Operating System"""
    if ctx.invoked_subcommand is None:
        console.print(
            Panel(
                Text("Mekong CLI: RaaS Agency Operating System", style="bold green"),
                title="🚀 Genesis",
                border_style="green",
            )
        )
        console.print(
            "\n[dim]Use[/dim] [bold cyan]mekong --help[/bold cyan] [dim]to see available commands[/dim]"
        )


if __name__ == "__main__":
    app()
