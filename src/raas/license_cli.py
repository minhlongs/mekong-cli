# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS License CLI — License key management and verification

Commands:
- mekong license check — Check current license status
- mekong license generate — Generate new license key
- mekong license validate — Validate a license key
"""
from __future__ import annotations

import os

from rich.console import Console
from rich.table import Table
import typer

from src.lib.raas_gate import PREMIUM_FEATURES, LicenseService, LicenseTier
from src.raas.license_cli_helpers import TIER_DISPLAY, _generate_key

console = Console()
app = typer.Typer(help="RaaS License Management")


@app.command("check")
def check_license():
    """Check current license status."""
    service = LicenseService.getInstance()
    validation = service.validateSync()

    table = Table(title="📜 RaaS License Status", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Tier", TIER_DISPLAY.get(validation.tier, validation.tier.upper()))
    table.add_row("Valid", "✅ Yes" if validation.valid else "❌ No")
    table.add_row("Features", f"{len(validation.features)} enabled")

    console.print(table)

    if validation.features:
        console.print("\n[bold]Enabled Features:[/bold]")
        for feature in validation.features:
            console.print(f"  • {feature}")

    console.print("\n[bold]Tier Comparison:[/bold]")
    console.print(f"  FREE: {len(PREMIUM_FEATURES['free'])} features")
    console.print(f"  PRO: {len(PREMIUM_FEATURES['pro'])} features")
    console.print(f"  ENTERPRISE: {len(PREMIUM_FEATURES['enterprise'])} features")

    if not validation.valid:
        console.print(
            "\n[yellow]⚠️  No valid license found.[/yellow]\n"
            "Set [bold]RAAS_LICENSE_KEY[/bold] environment variable to unlock premium features.\n"
            "Generate a key: [bold]mekong license generate --tier pro[/bold]"
        )


@app.command("generate")
def generate_license(
    tier: str = typer.Option("pro", "--tier", "-t", help="License tier: pro or enterprise"),
    tenant_id: str = typer.Option(None, "--tenant", help="Tenant ID to embed in license"),
    quantity: int = typer.Option(1, "--quantity", "-q", help="Number of keys to generate"),
):
    """Generate new license key(s)."""
    tier_lower = tier.lower()
    if tier_lower not in ("pro", "enterprise"):
        console.print(f"[red]Error:[/red] Invalid tier '{tier}'. Must be 'pro' or 'enterprise'.")
        raise typer.Exit(1)

    license_tier: LicenseTier = tier_lower  # type: ignore
    tier_upper = tier_lower.upper()

    console.print(f"\n[bold]Generating {quantity} {tier_upper} license key(s)...[/bold]\n")

    for i in range(quantity):
        key = _generate_key(license_tier, tenant_id)
        console.print(f"[green]Key {i + 1}:[/green]")
        console.print(f"  [cyan]{key}[/cyan]")
        console.print(f"  Tier: {tier_upper}")
        if tenant_id:
            console.print(f"  Tenant: {tenant_id}")
        console.print()

    console.print(
        "[yellow]⚠️  Keep these keys secure![/yellow]\n"
        "Add to .env: [bold]RAAS_LICENSE_KEY=your_key[/bold]"
    )


@app.command("validate")
def validate_license(
    key: str = typer.Argument(None, help="License key to validate"),
    from_env: bool = typer.Option(True, "--env", "-e", help="Read from RAAS_LICENSE_KEY env var"),
):
    """Validate a license key."""
    service = LicenseService.getInstance()

    if from_env or not key:
        key = os.getenv("RAAS_LICENSE_KEY", "")
        if not key:
            console.print("[red]Error:[/red] No license key provided and RAAS_LICENSE_KEY not set.")
            raise typer.Exit(1)

    validation = service.validateSync(key)

    if validation.valid:
        console.print(f"\n[green]✅ Valid {validation.tier.upper()} license![/green]")
        console.print(f"Features enabled: {len(validation.features)}")
    else:
        console.print("\n[red]❌ Invalid or missing license.[/red]")
        console.print(f"Tier: {validation.tier.upper()} (limited access)")

    console.print("\n[bold]Available Features:[/bold]")
    for feature in validation.features:
        console.print(f"  ✓ {feature}")


@app.command("features")
def list_features():
    """List all premium features by tier."""
    console.print("\n[bold]📦 RaaS Premium Features[/bold]\n")

    for tier_name, features in PREMIUM_FEATURES.items():
        console.print(
            f"[bold]{TIER_DISPLAY.get(tier_name, tier_name.upper())}[/bold] ({len(features)} features)"
        )
        for feature in features:
            console.print(f"  • {feature}")
        console.print()


__all__ = [
    "console",
    "app",
    "TIER_DISPLAY",
    "_generate_key",
    "check_license",
    "generate_license",
    "validate_license",
    "list_features",
]

if __name__ == "__main__":
    app()
