# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tier Admin CLI — ROIaaS Phase 6."""

import asyncio
from typing import Optional

from rich.console import Console
from rich.table import Table
import typer

from src.commands.tier_admin_overrides import (
    enterprise_show, list_overrides, remove_override, set_override,
)

console = Console()
app = typer.Typer(name="tier-admin", help="Manage tier rate limit configurations")


@app.command("list")
def list_configs() -> None:
    """List all tier rate limit configurations."""
    from src.db.tier_config_repository import get_repository

    console.print("[bold cyan]Tier Rate Limit Configurations[/bold cyan]\n")
    try:
        configs = asyncio.run(get_repository().get_all_configs())
        if not configs:
            console.print("[yellow]No tier configurations found in database.[/yellow]\n\n[dim]Using default configurations from src/lib/tier_config.py[/dim]")
            _show_default_configs()
            return

        for tier_name, presets in sorted(configs.items()):
            table = Table(title=f"Tier: {tier_name.upper()}", show_lines=True)
            for col, st in [("Preset", "cyan"), ("Rate Limit", "green"), ("Window (seconds)", "yellow")]:
                table.add_column(col, style=st)
            for preset_name, config in sorted(presets.items()):
                table.add_row(preset_name, str(config.rate_limit), str(config.window_seconds))
            console.print(table)
            console.print()
    except Exception as e:
        console.print(f"[red]Error loading configs:[/red] {e}\n\n[dim]Showing default configurations:[/dim]")
        _show_default_configs()


def _show_default_configs() -> None:
    """Show default tier configurations from module."""
    from engine.billing.tier_config import DEFAULT_TIER_CONFIGS, Tier

    for tier, config in DEFAULT_TIER_CONFIGS.items():
        tier_name = tier.value if isinstance(tier, Tier) else tier
        table = Table(title=f"Tier: {tier_name.upper()} (Default)", show_lines=True)
        for col, st in [("Preset", "cyan"), ("Requests/Min", "green"), ("Burst Size", "yellow")]:
            table.add_column(col, style=st)
        for preset_name, preset_config in [
            ("auth_login", config.auth_login), ("auth_callback", config.auth_callback),
            ("auth_refresh", config.auth_refresh), ("api_default", config.api_default),
        ]:
            table.add_row(preset_name, str(preset_config.requests_per_minute), str(preset_config.burst_size))
        console.print(table)
        console.print()


@app.command("get")
def get_config(tier: str) -> None:
    """Get configuration for a specific tier."""
    from src.db.tier_config_repository import get_repository

    console.print(f"[bold cyan]Configuration for Tier: {tier.upper()}[/bold cyan]\n")
    try:
        repo = get_repository()
        configs = {}
        for preset in ["auth_login", "auth_callback", "auth_refresh", "api_default"]:
            config = asyncio.run(repo.get_config(tier.lower(), preset))
            if config:
                configs[preset] = config

        if not configs:
            console.print(f"[yellow]No database config found for tier '{tier}'.[/yellow]\n\n[dim]Showing default configuration:[/dim]\n")
            _show_default_tier_config(tier)
            return

        table = Table(show_header=True)
        table.add_column("Preset", style="cyan")
        table.add_column("Rate Limit", style="green")
        table.add_column("Window (seconds)", style="yellow")
        for preset, config in sorted(configs.items()):
            table.add_row(preset, str(config.rate_limit), str(config.window_seconds))
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        _show_default_tier_config(tier)


def _show_default_tier_config(tier: str) -> None:
    """Show default configuration for a tier."""
    from engine.billing.tier_config import get_tier_config

    try:
        config = get_tier_config(tier)
        table = Table(show_header=True)
        table.add_column("Preset", style="cyan")
        table.add_column("Requests/Min", style="green")
        table.add_column("Burst Size", style="yellow")
        for preset_name, preset_config in [
            ("auth_login", config.auth_login),
            ("auth_callback", config.auth_callback),
            ("auth_refresh", config.auth_refresh),
            ("api_default", config.api_default),
        ]:
            table.add_row(preset_name, str(preset_config.requests_per_minute), str(preset_config.burst_size))
        console.print(table)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


@app.command("set")
def set_config(
    tier: str,
    preset: str,
    rate_limit: int = typer.Argument(..., help="Rate limit (requests per window)"),
    window_seconds: int = typer.Argument(60, help="Window size in seconds (default: 60)"),
) -> None:
    """Set rate limit configuration for a tier preset."""
    from engine.billing.tier_config import Tier
    from src.db.tier_config_repository import get_repository

    valid_tiers = [t.value for t in Tier]
    if tier.lower() not in valid_tiers:
        console.print(f"[red]Invalid tier '{tier}'.[/red]\n[dim]Valid tiers: {valid_tiers}[/dim]")
        raise typer.Exit(1)

    valid_presets = ["auth_login", "auth_callback", "auth_refresh", "api_default"]
    if preset.lower() not in valid_presets:
        console.print(f"[red]Invalid preset '{preset}'.[/red]\n[dim]Valid presets: {valid_presets}[/dim]")
        raise typer.Exit(1)

    if rate_limit < 1:
        console.print("[red]Rate limit must be at least 1.[/red]")
        raise typer.Exit(1)

    try:
        repo = get_repository()
        config = asyncio.run(repo.update_config(tier.lower(), preset.lower(), rate_limit, window_seconds))
        console.print("[bold green]✓ Configuration updated![/bold green]\n")
        console.print(f"  [cyan]Tier:[/cyan] {config.tier}\n  [cyan]Preset:[/cyan] {config.preset}")
        console.print(f"  [cyan]Rate Limit:[/cyan] {config.rate_limit} requests / {config.window_seconds}s")
        console.print(f"  [cyan]Window:[/cyan] {config.window_seconds} seconds")

        from src.lib.rate_limiter_factory import invalidate_cache
        invalidate_cache(tier.lower())
    except Exception as e:
        console.print(f"[red]Error updating config:[/red] {e}")
        raise typer.Exit(1)


app.command("override")(set_override)
app.command("overrides")(list_overrides)
app.command("remove-override")(remove_override)
app.command("enterprise")(enterprise_show)

__all__ = [
    "Optional", "_show_default_configs", "_show_default_tier_config", "app",
    "console", "enterprise_show", "get_config", "list_configs", "list_overrides",
    "remove_override", "set_config", "set_override",
]
