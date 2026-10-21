# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI Config Command - Manage environment variables and API keys
"""

import os
from pathlib import Path

import typer
from dotenv import dotenv_values, load_dotenv, set_key
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.commands.config_helpers import (
    mask_value,
    run_config_export,
    run_config_validate,
)

app = typer.Typer(name="config", help="Manage environment variables and API keys")
console = Console()

ENV_FILE = Path.cwd() / ".env"


@app.command()
def init() -> None:
    """Initialize .env file with required variables"""
    console.print(Panel("🔧 Mekong CLI Configuration Setup", border_style="cyan"))

    if not ENV_FILE.exists():
        ENV_FILE.touch()
        console.print("[green]✓[/green] Created .env file")

    required_vars = {"LLM_BASE_URL": "", "LLM_API_KEY": "", "LLM_MODEL": ""}
    load_dotenv(ENV_FILE)
    console.print("\n[bold]Configure required environment variables:[/bold]\n")

    for var_name, default_value in required_vars.items():
        current_value = os.getenv(var_name, "")
        if current_value:
            console.print(f"[dim]{var_name} = {mask_value(current_value)} (already set)[/dim]")
            if Confirm.ask(f"  Update {var_name}?", default=False):
                new_value = Prompt.ask(f"  Enter {var_name}", default=default_value)
                set_key(str(ENV_FILE), var_name, new_value)
                console.print(f"[green]✓[/green] Updated {var_name}")
        else:
            new_value = Prompt.ask(f"  Enter {var_name}", default=default_value)
            set_key(str(ENV_FILE), var_name, new_value)
            console.print(f"[green]✓[/green] Set {var_name}")

    console.print(
        Panel(
            "[green]Configuration initialized![/green]\n\n"
            "Run [bold]mekong status health[/bold] to verify setup",
            border_style="green",
        )
    )


@app.command()
def show() -> None:
    """Show current configuration (masked)"""
    load_dotenv(ENV_FILE)
    console.print(Panel("🔐 Current Configuration", border_style="blue"))

    key_vars = [
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_API_KEY",
        "MEKONG_API_TOKEN",
        "MEKONG_TELEGRAM_TOKEN",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
    ]

    table = Table(title="Environment Variables")
    table.add_column("Variable", style="cyan")
    table.add_column("Value (masked)", style="green")
    table.add_column("Source", style="dim")

    for var_name in key_vars:
        value = os.getenv(var_name, "")
        if value:
            source = "local" if os.getenv(f"LOCAL_{var_name}") else "system"
            table.add_row(var_name, mask_value(value), source)
        else:
            table.add_row(var_name, "[red](not set)[/red]", "-")

    console.print(table)
    console.print(f"\n[bold]Env file:[/bold] {ENV_FILE.absolute()}")
    if ENV_FILE.exists():
        console.print("[green]✓ exists[/green]")
    else:
        console.print("[yellow]⚠ does not exist - run 'mekong config init'[/yellow]")


@app.command()
def get(key: str) -> None:
    """Get a specific config value"""
    load_dotenv(ENV_FILE)
    value = os.getenv(key, "")
    if not value:
        console.print(f"[yellow]'{key}' is not set[/yellow]")
    else:
        is_secret = any(s in key.lower() for s in ("key", "token", "secret"))
        if is_secret:
            console.print(f"[bold]{key}:[/bold] {mask_value(value)}")
            if Confirm.ask("Show full value?", default=False):
                console.print(f"[dim]{value}[/dim]")
        else:
            console.print(f"[bold]{key}:[/bold] {value}")


@app.command()
def set(key: str, value: str) -> None:
    """Set a config value"""
    if not ENV_FILE.exists():
        ENV_FILE.touch()
        console.print(f"[green]✓[/green] Created {ENV_FILE}")

    set_key(str(ENV_FILE), key, value)
    masked = mask_value(value) if "key" in key.lower() or "token" in key.lower() else value
    console.print(f"[green]✓[/green] Set {key} = {masked}")


@app.command()
def unset(key: str) -> None:
    """Remove a config value"""
    if not ENV_FILE.exists():
        console.print("[yellow].env file does not exist[/yellow]")
        return

    env_vars = dotenv_values(str(ENV_FILE))
    if key not in env_vars:
        console.print(f"[yellow]'{key}' not found in .env[/yellow]")
        return

    del env_vars[key]
    ENV_FILE.write_text("")
    for k, v in env_vars.items():
        set_key(str(ENV_FILE), k, v or "")
    console.print(f"[green]✓[/green] Unset {key}")


@app.command()
def validate() -> None:
    """Validate configuration and check for issues"""
    run_config_validate()


@app.command()
def export(output: str = typer.Option(None, "--output", "-o", help="Output file path")) -> None:
    """Export configuration to file (excluding secrets)"""
    run_config_export(output=output)


def main():
    """Entry point for config subcommands"""
    app()


if __name__ == "__main__":
    app()
