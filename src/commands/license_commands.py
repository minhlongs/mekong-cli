# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License Management Commands — ROIaaS Phase 6."""

import json
import os
from pathlib import Path
from typing import Optional

from engine.license.license_generator import (
    TIER_LIMITS, generate_license, get_tier_limits, validate_license,
)
from engine.payments.usage_meter import get_meter, get_usage_summary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.license_usage_helpers import (
    _display_gateway_usage_report, _show_local_usage_report, _show_mock_usage_report, report, usage,
)
from src.commands.license_validation_helpers import (
    _show_dashboard_link, _validate_local, _validate_with_gateway,
)
from src.core.gateway_client import get_gateway_client
from src.core.raas_auth import get_auth_client

console = Console()
app = typer.Typer(help="🔑 License key management with RaaS Gateway integration")


@app.command()
def generate(
    tier: str = typer.Option("trial", "--tier", "-t", help="License tier (free/trial/pro/enterprise)"),
    email: str = typer.Option(..., "--email", "-e", help="User email for license"),
    days: int = typer.Option(None, "--days", "-d", help="Expiry in days (for trial tier)"),
) -> None:
    """Generate a new license key."""
    try:
        key = generate_license(tier, email, days)
        limits = get_tier_limits(tier)
        daily_str = f"{limits['commands_per_day'] if limits['commands_per_day'] >= 0 else 'unlimited'} commands"
        expiry_str = f"[dim]Expiry: {days} days[/dim]" if days else "[dim]Expiry: None[/dim]"
        msg = f"[bold green]{key}[/bold green]\n\n[dim]Tier: {tier}[/dim]\n[dim]Email: {email}[/dim]\n[dim]Daily Limit: {daily_str}[/dim]\n{expiry_str}"
        console.print(Panel(msg, title="🔑 License Key Generated", border_style="green"))
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def validate(
    key: Optional[str] = typer.Argument(None, help="License key to validate"),
    gateway: bool = typer.Option(False, "--gateway", "-g", help="Validate against RaaS Gateway (Phase 6)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation info"),
) -> None:
    """Validate a license key (local or gateway-based)."""
    license_key = key or os.getenv("RAAS_LICENSE_KEY")
    if not license_key:
        console.print("[bold red]✗ No license key provided[/bold red]\nUsage: mekong license validate [KEY] [--gateway]")
        raise typer.Exit(code=1)

    local_test = os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"
    if gateway and not local_test:
        _validate_with_gateway(license_key, verbose)
    else:
        _validate_local(license_key, verbose, gateway_mode=gateway)


@app.command()
def revoke(
    key: str = typer.Argument(..., help="License key to revoke"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Revoke a license key (add to revocation list)."""
    if not force and not typer.confirm(f"Are you sure you want to revoke this key?\n\n{key}"):
        console.print("[dim]Cancelled[/dim]")
        raise typer.Exit(code=0)

    revoked_path = Path.home() / ".mekong" / "revoked.json"
    revoked_path.parent.mkdir(parents=True, exist_ok=True)
    revoked = json.loads(revoked_path.read_text()) if revoked_path.exists() else []
    parts = key.split("-")
    key_id = parts[2] if len(parts) >= 3 else key
    if key_id not in revoked:
        revoked.append(key_id)
        revoked_path.write_text(json.dumps(revoked, indent=2))
    console.print(f"[bold green]✅ Key revoked:[/bold green] {key_id}")


@app.command()
def status(key: str = typer.Option(None, "--key", "-k", help="License key to check status for")) -> None:
    """Show license status and usage."""
    license_key = key or typer.Option(os.getenv("RAAS_LICENSE_KEY", ""), help="License key")
    if not license_key:
        console.print("[bold red]No license key provided.[/bold red]\nSet RAAS_LICENSE_KEY env var or use --key flag.")
        raise typer.Exit(code=1)

    is_valid, info, error = validate_license(license_key)
    if not is_valid:
        console.print(f"[bold red]Invalid key:[/bold red] {error}")
        raise typer.Exit(code=1)

    tier = info.get("tier", "unknown") if info else "unknown"
    key_id = info.get("key_id", "unknown") if info else "unknown"
    limits = get_tier_limits(tier)
    try:
        usage_data = get_usage_summary(key_id)
    except Exception:
        usage_data = {}

    table = Table(title="License Status", show_lines=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold")
    for prop, val in [
        ("Status", "✅ Valid" if is_valid else "❌ Invalid"), ("Tier", tier), ("Key ID", key_id),
        ("Daily Limit", str(limits["commands_per_day"]) if limits["commands_per_day"] >= 0 else "Unlimited"),
        ("Commands Today", str(usage_data.get("commands_today", 0))),
        ("Total Commands", str(usage_data.get("total_commands", 0))),
        ("Remaining", str(usage_data.get("remaining", "N/A"))),
    ]:
        table.add_row(prop, val)
    console.print(table)


@app.command()
def tiers() -> None:
    """Show available license tiers and limits."""
    table = Table(title="License Tiers", show_lines=True)
    table.add_column("Tier", style="cyan", justify="center")
    table.add_column("Commands/Day", justify="right")
    table.add_column("Max Days", justify="right")
    table.add_column("Description", style="dim")
    tier_descriptions = {
        "free": "Basic access for individuals", "trial": "7-day trial with full features",
        "pro": "Professional use with high limits", "enterprise": "Unlimited access for teams",
    }
    for tier, limits in TIER_LIMITS.items():
        daily, max_days = limits["commands_per_day"], limits["max_days"]
        table.add_row(tier, str(daily) if daily >= 0 else "Unlimited", str(max_days) if max_days else "Unlimited", tier_descriptions.get(tier, ""))
    console.print(table)


app.command()(usage)
app.command("report")(report)


@app.command("features")
def features() -> None:
    from src.core.feature_gates import show_features_status
    show_features_status()


@app.command("permissions")
def permissions() -> None:
    from src.core.permission_registry import show_permissions_status
    show_permissions_status()


@app.command("entitlement")
def entitlement() -> None:
    from src.core.entitlement_enforcer import show_entitlement_status
    show_entitlement_status()


__all__ = [
    "TIER_LIMITS", "_display_gateway_usage_report", "_show_dashboard_link",
    "_show_local_usage_report", "_show_mock_usage_report", "_validate_local",
    "_validate_with_gateway", "app", "console", "entitlement", "features",
    "generate", "generate_license", "get_auth_client", "get_gateway_client",
    "get_meter", "get_tier_limits", "get_usage_summary", "permissions",
    "report", "revoke", "status", "tiers", "usage", "validate", "validate_license",
]
