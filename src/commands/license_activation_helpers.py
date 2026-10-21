# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for License Activation CLI commands."""

from __future__ import annotations

import json
from rich.panel import Panel
from rich.table import Table


def _mod():
    import src.commands.license_activation as mod

    return mod


def _display_license_summary(license_data, verbose: bool = False) -> None:
    """Display license activation summary."""
    m = _mod()
    tier_color = {
        "free": "dim",
        "pro": "green",
        "enterprise": "bold magenta",
        "unlimited": "bold cyan",
    }.get(license_data.tier.lower(), "white")

    summary = Table(show_header=False, box=None)
    summary.add_column("Label", style="dim")
    summary.add_column("Value", style=tier_color)

    summary.add_row("Tenant", license_data.tenant_id)
    summary.add_row("Tier", license_data.tier.upper())
    summary.add_row("Rate Limit", f"{license_data.rate_limit}/min")

    if license_data.days_until_expiry:
        summary.add_row("Expires In", f"{license_data.days_until_expiry} days")
    elif license_data.expires_at:
        summary.add_row("Expires", "Never")

    m.console.print(summary)

    if verbose:
        if license_data.features:
            m.console.print(f"\n[dim]Features: {', '.join(license_data.features)}[/dim]")
        m.console.print("[dim]Gateway: https://api.cashclaw.cc[/dim]\n")


def render_license_status(verbose: bool = False, json_output: bool = False) -> None:
    """Render current license status details."""
    from src.core.license_manager import get_license_manager

    m = _mod()
    m.console.print("[bold cyan]📋 License Status[/bold cyan]\n")

    license_manager = get_license_manager()
    license_data = license_manager.get_license()

    if not license_data:
        m.console.print(
            Panel(
                "[yellow]No license activated[/yellow]\n\n"
                "Activate your license with:\n"
                "  [cyan]mekong license-activate mk_your_key[/cyan]\n\n"
                "Or set environment variable:\n"
                "  [cyan]export RAAS_LICENSE_KEY=mk_your_key[/cyan]",
                title="No License",
                border_style="yellow",
            )
        )
        return

    if json_output:
        print(json.dumps(license_data.to_dict(), indent=2, default=str))
        return

    if license_data.is_expired:
        status = "❌ Expired"
        status_color = "red"
    elif license_data.days_until_expiry and license_data.days_until_expiry <= 7:
        status = f"⚠️ Expiring in {license_data.days_until_expiry} days"
        status_color = "yellow"
    else:
        status = "✅ Active"
        status_color = "green"

    m.console.print(f"[bold {status_color}]{status}[/bold {status_color}]\n")

    table = Table(title="License Details", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value", style="green")

    table.add_row("Tenant ID", license_data.tenant_id)
    table.add_row("Tier", license_data.tier.upper())
    table.add_row("Rate Limit", f"{license_data.rate_limit} requests/min")
    table.add_row("Max Payload", f"{license_data.max_payload_size:,} bytes")
    table.add_row("Retention", f"{license_data.retention_days} days")

    if license_data.features:
        table.add_row("Features", ", ".join(license_data.features))
    else:
        table.add_row("Features", "[dim]Default features[/dim]")

    if license_data.expires_at:
        table.add_row("Expires At", license_data.expires_at)
        if license_data.days_until_expiry is not None:
            table.add_row("Days Until Expiry", str(license_data.days_until_expiry))

    table.add_row("Activated At", license_data.activated_at)
    table.add_row("Last Validated", license_data.last_validated)

    m.console.print(table)

    if verbose:
        m.console.print(f"\n[dim]License file: {license_manager.license_path}[/dim]\n")
