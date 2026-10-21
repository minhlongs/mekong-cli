# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tenant overrides and enterprise commands for Tier Admin CLI."""

import asyncio
import sys
from typing import Optional

from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.tier_admin"]


def set_override(
    tenant_id: str,
    preset: str,
    custom_limit: int = typer.Argument(..., help="Custom rate limit"),
    custom_window: int = typer.Argument(60, help="Custom window in seconds (default: 60)"),
    tier: Optional[str] = typer.Option(None, "--tier", "-t", help="Optional tier override"),
) -> None:
    """Set custom rate limit override for a tenant."""
    from src.db.tier_config_repository import get_repository

    f = _facade()
    valid_presets = ["auth_login", "auth_callback", "auth_refresh", "api_default"]
    if preset.lower() not in valid_presets:
        f.console.print(f"[red]Invalid preset '{preset}'.[/red]\n[dim]Valid presets: {valid_presets}[/dim]")
        raise typer.Exit(1)

    if custom_limit < 1:
        f.console.print("[red]Custom limit must be at least 1.[/red]")
        raise typer.Exit(1)

    try:
        repo = get_repository()
        override = asyncio.run(
            repo.set_tenant_override(
                tenant_id=tenant_id,
                preset=preset.lower(),
                custom_limit=custom_limit,
                custom_window=custom_window,
                tier=tier.lower() if tier else None,
            )
        )

        f.console.print("[bold green]✓ Tenant override created![/bold green]\n")
        f.console.print(f"  [cyan]Tenant ID:[/cyan] {override.tenant_id}\n  [cyan]Preset:[/cyan] {override.preset}")
        f.console.print(f"  [cyan]Custom Limit:[/cyan] {override.custom_limit} requests / {override.custom_window}s")
        if override.tier:
            f.console.print(f"  [cyan]Tier Override:[/cyan] {override.tier}")
        if override.expires_at:
            f.console.print(f"  [cyan]Expires:[/cyan] {override.expires_at}")
    except Exception as e:
        f.console.print(f"[red]Error setting override:[/red] {e}")
        raise typer.Exit(1)


def list_overrides(
    tenant_id: Optional[str] = typer.Option(None, "--tenant", "-t", help="Filter by tenant ID"),
) -> None:
    """List all tenant rate limit overrides."""
    from src.db.tier_config_repository import get_repository

    f = _facade()
    f.console.print("[bold cyan]Tenant Rate Limit Overrides[/bold cyan]\n")

    try:
        repo = get_repository()
        overrides = asyncio.run(repo.get_all_tenant_overrides(tenant_id))

        if not overrides:
            msg = f"No overrides found for tenant '{tenant_id}'." if tenant_id else "No tenant overrides configured."
            f.console.print(f"[yellow]{msg}[/yellow]")
            return

        table = Table(show_header=True)
        for col, st in [("Tenant ID", "cyan"), ("Preset", "green"), ("Custom Limit", "yellow"), ("Window (s)", "magenta"), ("Tier Override", "blue"), ("Expires", "red")]:
            table.add_column(col, style=st)

        for override in overrides:
            table.add_row(
                override.tenant_id,
                override.preset,
                str(override.custom_limit) if override.custom_limit else "-",
                str(override.custom_window),
                override.tier or "-",
                override.expires_at or "-",
            )
        f.console.print(table)
    except Exception as e:
        f.console.print(f"[red]Error loading overrides:[/red] {e}")


def remove_override(
    tenant_id: str,
    preset: str,
) -> None:
    """Remove a tenant rate limit override."""
    from src.db.tier_config_repository import get_repository

    f = _facade()
    valid_presets = ["auth_login", "auth_callback", "auth_refresh", "api_default"]
    if preset.lower() not in valid_presets:
        f.console.print(f"[red]Invalid preset '{preset}'.[/red]\n[dim]Valid presets: {valid_presets}[/dim]")
        raise typer.Exit(1)

    try:
        repo = get_repository()
        deleted = asyncio.run(repo.delete_tenant_override(tenant_id, preset.lower()))
        if deleted:
            f.console.print(f"[bold green]✓ Override removed for {tenant_id} ({preset})[/bold green]")
        else:
            f.console.print(f"[yellow]No override found for {tenant_id} ({preset})[/yellow]")
    except Exception as e:
        f.console.print(f"[red]Error removing override:[/red] {e}")
        raise typer.Exit(1)


def enterprise_show(
    tier: str = typer.Option("enterprise", "--tier", "-t", help="Tier to display enterprise details for"),
) -> None:
    """Show enterprise SLA, support channel, and enterprise-specific limits."""
    from engine.billing.tier_config import Tier

    f = _facade()
    try:
        target = Tier(tier.lower())
    except ValueError:
        f.console.print(f"[red]Invalid tier '{tier}'.[/red]\n[dim]Valid tiers: {[t.value for t in Tier]}[/dim]")
        raise typer.Exit(1)

    f.console.print(f"[bold cyan]Enterprise Details — {tier.upper()}[/bold cyan]")
    if target != Tier.ENTERPRISE:
        f.console.print(f"[yellow]Warning:[/yellow] {tier.upper()} is not the enterprise tier. Showing base configuration only.")

    try:
        from src.auth.enterprise import get_enterprise_config
        cfg = get_enterprise_config()
    except ImportError:
        cfg = None

    table = Table(show_header=False)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_row("Tier", tier.upper())
    table.add_row("SLA Response Window", f"{cfg.sla_response_hours if cfg else '4'} hours")
    table.add_row("Support Channel", cfg.support_channel or "Not configured")
    table.add_row("Audit Retention", f"{cfg.audit_retention_days if cfg else '90'} days")
    sso_str = ", ".join(p.provider_id for p in (cfg.sso_providers.values() if cfg else []) if p.enabled) or "None enabled"
    table.add_row("SSO", sso_str)
    table.add_row("License Enforcement", "Enabled via engine.license.license_gate_middleware when MEKONG_MINIMUM_TIER is set")
    f.console.print(table)
