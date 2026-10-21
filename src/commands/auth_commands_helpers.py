# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for Mekong CLI authentication commands."""

from __future__ import annotations

import typer
from rich.table import Table


def _mod():
    import src.commands.auth_commands as mod

    return mod


def run_auth_status() -> None:
    """Display current authentication status."""
    m = _mod()
    m.console.print("[bold blue]Mekong CLI Auth Status[/bold blue]\n")

    storage = m.get_secure_storage()
    license_key = storage.get_license()

    if not license_key:
        m.console.print("[yellow]Not logged in[/yellow]\n")
        m.console.print(
            "Run [cyan]mekong login[/cyan] to login with your license key.\n"
        )
        raise typer.Exit(1)

    masked = (
        license_key[:8] + "..." + license_key[-4:]
        if len(license_key) > 12
        else "***"
    )

    m.console.print("[dim]Checking license status with gateway...[/dim]\n")

    try:
        client = m.get_gateway_client()
        result = client.verify_license(license_key)

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="dim")
        table.add_column("Value")

        table.add_row(
            "Status:",
            "[green]✓ Logged in[/green]" if result.valid else "[red]✗ Invalid[/red]",
        )
        table.add_row("License:", masked)

        if result.tier:
            table.add_row("Tier:", result.tier.upper())
        if result.email:
            table.add_row("Email:", result.email)
        if result.expires_at:
            table.add_row("Expires:", result.expires_at)
        if result.features:
            table.add_row("Features:", ", ".join(result.features))

        m.console.print(table)

        if not result.valid:
            m.console.print(
                f"\n[red]⚠ License invalid: {result.error}[/red]\n"
                "Run [cyan]mekong login[/cyan] to update your license.\n"
            )
            raise typer.Exit(1)

        m.console.print("\n[dim]✓ Your license is active and valid.[/dim]\n")

    except m.GatewayClientError:
        m.console.print(
            "[yellow]⚠ Gateway unreachable - showing local status only[/yellow]\n"
        )

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="dim")
        table.add_column("Value")

        table.add_row("Status:", "[yellow]Unknown (offline)[/yellow]")
        table.add_row("License:", masked)
        table.add_row("Storage:", "Secure storage configured")

        m.console.print(table)
        m.console.print(
            "\n[dim]Tip: Connect to internet to verify license status.[/dim]\n"
        )


def run_verify_license(license_key: str) -> None:
    """Verify a license key without storing it."""
    m = _mod()
    m.console.print("[bold blue]License Verification[/bold blue]\n")

    try:
        client = m.get_gateway_client()
        result = client.verify_license(license_key)

        if result.valid:
            m.console.print("[bold green]✓ Valid License[/bold green]\n")

            table = Table(show_header=True, box=None, padding=(0, 1))
            table.add_column("Attribute", style="dim")
            table.add_column("Value")

            if result.tier:
                table.add_row("Tier", result.tier.upper())
            if result.email:
                table.add_row("Email", result.email)
            if result.expires_at:
                table.add_row("Expires", result.expires_at)
            if result.features:
                table.add_row("Features", ", ".join(result.features))

            m.console.print(table)
        else:
            m.console.print("[red]✗ Invalid License[/red]\n")
            m.console.print(f"[dim]Error: {result.error}[/dim]\n")
            raise typer.Exit(1)

    except m.GatewayClientError as e:
        m.console.print(f"[red]✗ Verification failed: {str(e)}[/red]\n")
        raise typer.Exit(1)
