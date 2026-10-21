# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS License Validation Command — Phase 1 Gate

Command: mekong validate-license

Validates RaaS license key against RaaS Gateway with certificate-based authentication.
"""

import os
from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.panel import Panel

from src.commands.raas_validate_helpers import (
    _show_failure_result,
    _show_license_status,
    _show_success_result,
)

console = Console()

app = typer.Typer(help="RaaS License validation commands")


@app.command("validate-license")
def validate_license(
    license_key: str = typer.Option(
        None,
        "--key",
        "-k",
        help="License key (mk_* or JWT format). Uses RAAS_LICENSE_KEY env if not provided.",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        "-c",
        help="Check license status without validation",
    ),
    renew: bool = typer.Option(
        False,
        "--renew",
        "-r",
        help="Force certificate renewal before validation",
    ),
    no_certificate: bool = typer.Option(
        False,
        "--no-cert",
        help="Disable certificate-based authentication",
    ),
):
    """
    Validate RaaS license key against RaaS Gateway.

    Uses certificate-based authentication by default.
    """
    from src.core.raas_auth import RaaSAuthClient

    console.print("[bold cyan]=== RaaS License Validation ===[/bold cyan]\n")

    if not license_key:
        license_key = os.getenv("RAAS_LICENSE_KEY")

    if not license_key and not check:
        console.print(
            "[red]Error:[/red] No license key provided.\n"
            "Set [cyan]RAAS_LICENSE_KEY[/cyan] environment variable or use [cyan]--key[/cyan] option.\n"
        )
        raise typer.Exit(1)

    use_certificate_auth = (
        not no_certificate
        and os.getenv("RAAS_USE_CERTIFICATE_AUTH", "true").lower() != "false"
    )

    try:
        client = RaaSAuthClient(use_certificate_auth=use_certificate_auth)
    except Exception as e:
        console.print(f"[red]Error initializing auth client: {e}[/red]")
        raise typer.Exit(1)

    if check:
        _show_license_status(client)
        return

    if renew and use_certificate_auth:
        console.print("[dim]Rotating certificate...[/dim]")
        try:
            client.rotate_certificate()
            console.print("[green]✓ Certificate rotated[/green]\n")
        except Exception as e:
            console.print(f"[yellow]⚠ Certificate rotation failed: {e}[/yellow]\n")

    if use_certificate_auth:
        cert_status = client.get_certificate_status()
        if cert_status.get("has_certificate"):
            console.print(
                f"[dim]Certificate: {cert_status.get('certificate_id', 'N/A')}[/dim]\n"
            )

    console.print("[dim]Validating license with RaaS Gateway...[/dim]")
    console.print(f"[dim]Gateway: {client.gateway_url}[/dim]\n")

    result = client.validate_credentials(license_key)

    if result.valid and result.tenant:
        _show_success_result(result, client)
        raise typer.Exit(0)
    else:
        _show_failure_result(result)
        raise typer.Exit(1)


@app.command("license-status")
def license_status():
    """Show current RaaS license status."""
    from src.core.raas_auth import RaaSAuthClient

    try:
        client = RaaSAuthClient()
        _show_license_status(client)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


__all__ = [
    "Console",
    "Panel",
    "_show_failure_result",
    "_show_license_status",
    "_show_success_result",
    "app",
    "console",
    "datetime",
    "license_status",
    "timezone",
    "validate_license",
]
