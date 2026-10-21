# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License validation helpers for License Management Commands."""

import sys

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.license_commands"]


def _show_dashboard_link(tenant_id: str, tier: str) -> None:
    """Phase 6.4: Show dashboard handoff link."""
    f = _facade()
    dashboard_url = f"https://www.mekongmind.com/dashboard/{tenant_id}/license"

    f.console.print()
    f.console.print(
        Panel(
            f"[bold]Manage your license:[/bold]\n"
            f"[cyan]{dashboard_url}[/cyan]\n\n"
            f"[dim]Tier: {tier.upper()} | Tenant: {tenant_id}[/dim]",
            title="🌐 AgencyOS Dashboard",
            border_style="blue",
        )
    )


def _validate_local(key: str, verbose: bool, gateway_mode: bool = False) -> None:
    """Local license validation (fallback)."""
    f = _facade()
    local_test = f.os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"

    if local_test:
        auth_client = f.get_auth_client()
        result = auth_client.validate_credentials(key)

        if result.valid and result.tenant:
            tenant = result.tenant
            f.console.print(f"[green]✓ Valid {tenant.tier.upper()} license (Local Test Mode)[/green]\n")

            table = Table(title="License Details", show_header=True)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Tenant ID", tenant.tenant_id)
            table.add_row("Tier", tenant.tier.upper())
            table.add_row("Role", tenant.role)
            table.add_row("Features", f"{len(tenant.features)} enabled")

            f.console.print(table)

            if tenant.features:
                f.console.print("\n[bold]Enabled Features:[/bold]")
                for feature in tenant.features[:5]:
                    f.console.print(f"  ✓ {feature}")

            f._show_dashboard_link(tenant.tenant_id, tenant.tier)
            return
        else:
            f.console.print(
                Panel(
                    f"[bold red]Local validation failed[/bold red]\n\n{result.error}",
                    title="❌ License Validation",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)

    is_valid, info, error = f.validate_license(key)

    if is_valid:
        tier = info.get("tier", "unknown") if info else "unknown"
        key_id = info.get("key_id", "unknown") if info else "unknown"
        limits = f.get_tier_limits(tier)

        panel_content = (
            f"[bold green]Valid License (Local)[/bold green]\n\n"
            f"Tier: [bold]{tier}[/bold]\n"
            f"Key ID: {key_id}\n"
            f"Daily Limit: {limits['commands_per_day'] if limits['commands_per_day'] >= 0 else 'unlimited'} commands"
        )

        if gateway_mode:
            panel_content += "\n\n[yellow]⚠ Gateway validation unavailable - using local fallback[/yellow]"

        f.console.print(
            Panel(
                panel_content,
                title="✅ License Validation",
                border_style="green",
            )
        )

        f._show_dashboard_link(key_id, tier)
    else:
        f.console.print(
            Panel(
                f"[bold red]Invalid License[/bold red]\n\n{error}",
                title="❌ License Validation",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)


def _validate_with_gateway(key: str, verbose: bool) -> None:
    """Phase 6.1: Gateway-based license validation."""
    f = _facade()
    f.console.print("[dim]Validating with RaaS Gateway...[/dim]\n")

    try:
        auth_client = f.get_auth_client()
        result = auth_client.validate_credentials(key)

        if result.valid and result.tenant:
            tenant = result.tenant
            f.console.print(f"[green]✓ Valid {tenant.tier.upper()} license[/green]\n")

            table = Table(title="License Details", show_header=True)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Tenant ID", tenant.tenant_id)
            table.add_row("Tier", tenant.tier.upper())
            table.add_row("Role", tenant.role)
            table.add_row("Features", f"{len(tenant.features)} enabled")

            if tenant.expires_at:
                table.add_row("Expires", tenant.expires_at.strftime("%Y-%m-%d %H:%M"))

            f.console.print(table)

            if tenant.features:
                f.console.print("\n[bold]Enabled Features:[/bold]")
                for feature in tenant.features[:10]:
                    f.console.print(f"  ✓ {feature}")
                if len(tenant.features) > 10:
                    f.console.print(f"  ... and {len(tenant.features) - 10} more")

            f._show_dashboard_link(tenant.tenant_id, tenant.tier)

            if verbose:
                gateway_info = auth_client.get_gateway_health()
                f.console.print(f"\n[dim]Gateway: {gateway_info.get('url', 'N/A')}[/dim]")
                f.console.print(f"[dim]Status: {gateway_info.get('status', 'N/A')}[/dim]")
        else:
            f.console.print(
                Panel(
                    f"[bold red]Gateway validation failed[/bold red]\n\n{result.error}",
                    title="❌ License Validation",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)

    except typer.Exit:
        raise
    except Exception as e:
        f.console.print(f"[yellow]⚠ Gateway validation failed: {e}[/yellow]")
        f.console.print("[dim]Falling back to local validation...[/dim]\n")
        f._validate_local(key, verbose, gateway_mode=True)
