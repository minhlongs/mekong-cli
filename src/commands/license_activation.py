# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
License Activation CLI Command — Phase 6

Commands:
    mekong license-activate <key>  - Activate license key
    mekong license-status          - Show current license status
    mekong license-deactivate      - Deactivate current license
"""

import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.commands.license_activation_helpers import (
    _display_license_summary,
    render_license_status,
)

console = Console()

app = typer.Typer(
    name="license-activation",
    help="🔑 License activation and management",
    rich_markup_mode="rich",
)


@app.command("activate")
def activate_license(
    license_key: Optional[str] = typer.Argument(None, help="RaaS License Key (mk_...)"),
    from_env: bool = typer.Option(
        False, "--from-env", "-e", help="Read license key from RAAS_LICENSE_KEY env var"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed activation information"
    ),
) -> None:
    """🔑 Activate RaaS license key."""
    from src.core.license_manager import LicenseData, get_license_manager
    from src.core.raas_auth import RaaSAuthClient

    console.print("[bold cyan]🔑 RaaS License Activation[/bold cyan]\n")

    if from_env:
        license_key = os.getenv("RAAS_LICENSE_KEY")
        if not license_key:
            console.print(
                "[bold red]✗ Error:[/bold red] RAAS_LICENSE_KEY not set\n"
                "[dim]Export your license key first:[/dim]\n"
                "  [cyan]export RAAS_LICENSE_KEY=mk_your_key[/cyan]\n"
            )
            raise SystemExit(1)
    elif not license_key:
        console.print(
            "[bold red]✗ Error:[/bold red] No license key provided\n"
            "[dim]Usage:[/dim]\n"
            "  [cyan]mekong license-activate mk_your_key[/cyan]\n\n"
            "[dim]Or use --from-env to read from RAAS_LICENSE_KEY[/dim]\n"
        )
        raise SystemExit(1)

    if not license_key.startswith("mk_"):
        console.print("[yellow]⚠ Warning:[/yellow] License key should start with 'mk_'\n")

    console.print("[dim]Step 1/3: Validating with RaaS Gateway...[/dim]")
    auth_client = RaaSAuthClient()
    result = auth_client.validate_credentials(license_key)

    if not result.valid:
        console.print(f"[bold red]✗ Validation failed: {result.error}[/bold red]\n")
        console.print("[dim]Get a license key from:[/dim]\n  [cyan]https://api.cashclaw.cc[/cyan]\n")
        raise SystemExit(1)

    console.print("[green]✓ License validated[/green]\n")
    console.print("[dim]Step 2/3: Storing license...[/dim]")
    license_manager = get_license_manager()

    license_data = LicenseData(
        license_key=license_key,
        tenant_id=result.tenant_id,
        tier=result.tier,
        features=result.features if hasattr(result, "features") else [],
        rate_limit=result.rate_limit if hasattr(result, "rate_limit") else 60,
        expires_at=result.expires_at.isoformat()
        if hasattr(result, "expires_at") and result.expires_at
        else None,
    )

    if not license_manager.save_license(license_data):
        console.print("[bold red]✗ Failed to save license[/bold red]\n")
        raise SystemExit(1)

    console.print("[green]✓ License stored[/green]\n")
    console.print("[dim]Step 3/3: Updating validation...[/dim]")
    license_manager.update_validation_timestamp()
    console.print("[green]✓ Activation complete[/green]\n")
    _display_license_summary(license_data, verbose)


@app.command("status")
def license_status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed license information"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """📋 Show current license status."""
    render_license_status(verbose=verbose, json_output=json_output)


@app.command("deactivate")
def deactivate_license(
    force: bool = typer.Option(False, "--force", "-f", help="Deactivate without confirmation"),
) -> None:
    """🚫 Deactivate current license."""
    from src.core.license_manager import get_license_manager

    console.print("[bold cyan]🚫 Deactivate License[/bold cyan]\n")

    license_manager = get_license_manager()
    license_data = license_manager.get_license()

    if not license_data:
        console.print("[yellow]No license to deactivate[/yellow]\n")
        return

    if not force:
        console.print(
            f"Current license: [cyan]{license_data.tenant_id}[/cyan] ({license_data.tier.upper()})\n"
        )
        if not typer.confirm("Are you sure you want to deactivate this license?"):
            console.print("[dim]Deactivation cancelled[/dim]\n")
            return

    if license_manager.clear_license():
        console.print(
            Panel(
                "[green]✓ License deactivated[/green]\n\n"
                "Activate a new license with:\n"
                "  [cyan]mekong license-activate mk_your_key[/cyan]",
                title="Success",
                border_style="green",
            )
        )
    else:
        console.print("[bold red]✗ Failed to deactivate license[/bold red]\n")


__all__ = [
    "Console",
    "Panel",
    "Table",
    "_display_license_summary",
    "activate_license",
    "app",
    "console",
    "deactivate_license",
    "license_status",
]
