# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage reporting and status helpers for License Management Commands."""

import random
import sys
from typing import Optional

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.license_commands"]


def usage(
    key: Optional[str] = typer.Option(None, "--key", "-k", help="License key to check usage for"),
    reset: bool = typer.Option(False, "--reset", help="Reset usage counter"),
) -> None:
    """Show or reset usage statistics."""
    f = _facade()
    license_key = key or f.os.getenv("RAAS_LICENSE_KEY", "")
    if not license_key:
        f.console.print("[bold red]No license key provided.[/bold red]\nSet RAAS_LICENSE_KEY env var or use --key flag.")
        raise typer.Exit(code=1)

    is_valid, info, _ = f.validate_license(license_key)
    if not is_valid:
        f.console.print(f"[bold red]Invalid key:[/bold red] {info}")
        raise typer.Exit(code=1)

    key_id = info.get("key_id", "unknown") if info else "unknown"
    if reset:
        if f.get_meter().reset_usage(key_id):
            f.console.print("[bold green]✅ Usage reset successfully[/bold green]")
        else:
            f.console.print("[bold yellow]⚠️  No usage record found[/bold yellow]")
        return

    try:
        usage_data = f.get_usage_summary(key_id)
        if "error" in usage_data:
            f.console.print(f"[bold yellow]⚠️  {usage_data['error']}[/bold yellow]")
        else:
            f.console.print(Panel(
                f"[bold]Key ID:[/bold] {usage_data.get('key_id', 'N/A')}\n"
                f"[bold]Tier:[/bold] {usage_data.get('tier', 'N/A')}\n"
                f"[bold]Commands Today:[/bold] {usage_data.get('commands_today', 0)}\n"
                f"[bold]Daily Limit:[/bold] {usage_data.get('daily_limit', 'N/A')}\n"
                f"[bold]Remaining:[/bold] {usage_data.get('remaining', 'N/A')}\n"
                f"[bold]Total Commands:[/bold] {usage_data.get('total_commands', 0)}",
                title="📊 Usage Statistics", border_style="blue",
            ))
    except Exception as e:
        f.console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


def report(
    key: Optional[str] = typer.Option(None, "--key", "-k", help="License key"),
    days: int = typer.Option(30, "--days", "-d", help="Number of days to report"),
) -> None:
    """Phase 6.2: Usage report from RaaS Gateway."""
    f = _facade()
    license_key = key or f.os.getenv("RAAS_LICENSE_KEY")
    if not license_key:
        f.console.print("[bold red]✗ No license key provided[/bold red]\nSet RAAS_LICENSE_KEY env var or use --key flag.")
        raise typer.Exit(code=1)

    if f.os.getenv("RAAS_LOCAL_TEST", "").lower() == "true":
        f.console.print("[yellow]⚠ Local test mode - showing mock data[/yellow]\n")
        f._show_mock_usage_report(license_key, days)
        return

    try:
        auth_client, gateway_client = f.get_auth_client(), f.get_gateway_client()
        result = auth_client.validate_credentials(license_key)
        if not result.valid:
            f.console.print(f"[bold red]✗ Invalid license:[/bold red] {result.error}")
            raise typer.Exit(code=1)

        f.console.print("[dim]Fetching usage report from RaaS Gateway...[/dim]\n")
        response = gateway_client.get("/v1/usage", params={"limit": days * 24, "offset": 0})
        if response.status_code == 200:
            f._display_gateway_usage_report(response.data, days)
        else:
            f.console.print(f"[yellow]⚠ Gateway returned {response.status_code} - showing local data[/yellow]")
            f._show_local_usage_report(license_key, days)
    except typer.Exit:
        raise
    except Exception as e:
        f.console.print(f"[yellow]⚠ Gateway error: {e}[/yellow]\n[dim]Showing local usage report...[/dim]\n")
        f._show_local_usage_report(license_key, days)


def _display_gateway_usage_report(data: dict, days: int) -> None:
    """Display usage report from gateway data."""
    f = _facade()
    summary, metrics, pagination = data.get("summary", {}), data.get("metrics", []), data.get("pagination", {})
    table = Table(title="📊 RaaS Usage Report", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for label, val in [
        ("Period", f"Last {days} days"), ("Total Requests", f"{summary.get('total_requests', 0):,}"),
        ("Total Payload", f"{summary.get('total_payload_size', 0):,} bytes"),
        ("Hours Active", f"{summary.get('total_hours', 0)}"), ("Data Points", f"{len(metrics)}"),
    ]:
        table.add_row(label, val)
    f.console.print(table)

    if metrics:
        endpoint_counts: dict = {}
        for metric in metrics:
            ep = metric.get("endpoint", "unknown")
            endpoint_counts[ep] = endpoint_counts.get(ep, 0) + metric.get("request_count", 0)
        if endpoint_counts:
            f.console.print("\n[bold]Endpoint Breakdown:[/bold]")
            endpoint_table = Table(show_header=True)
            endpoint_table.add_column("Endpoint", style="cyan")
            endpoint_table.add_column("Requests", style="green")
            for ep, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                endpoint_table.add_row(ep, f"{count:,}")
            f.console.print(endpoint_table)

    f._show_dashboard_link(data.get("tenant_id", "unknown"), "unknown")
    if pagination.get("has_more"):
        f.console.print(f"\n[dim]Showing {pagination.get('limit', 0)} of {pagination.get('total', 0)} records[/dim]")


def _show_local_usage_report(key: str, days: int) -> None:
    """Show local usage report as fallback."""
    f = _facade()
    is_valid, info, _ = f.validate_license(key)
    if not is_valid:
        f.console.print(f"[bold red]Invalid key:[/bold red] {info}")
        return

    key_id = info.get("key_id", "unknown") if info else "unknown"
    tier = info.get("tier", "unknown") if info else "unknown"
    try:
        usage_data = f.get_usage_summary(key_id)
        table = Table(title="📊 Local Usage Report", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        for label, val in [
            ("Period", f"Last {days} days (local)"), ("Key ID", key_id), ("Tier", tier),
            ("Commands Today", f"{usage_data.get('commands_today', 0):,}"),
            ("Total Commands", f"{usage_data.get('total_commands', 0):,}"),
            ("Daily Limit", str(usage_data.get("daily_limit", "N/A"))),
            ("Remaining", str(usage_data.get("remaining", "N/A"))),
        ]:
            table.add_row(label, val)
        f.console.print(table)
        f._show_dashboard_link(key_id, tier)
    except Exception as e:
        f.console.print(f"[bold red]Error:[/bold red] {e}")


def _show_mock_usage_report(key: str, days: int) -> None:
    """Show mock usage report for local testing."""
    f = _facade()
    f.console.print("[dim]Generating mock usage data...[/dim]\n")
    table = Table(title="📊 Mock Usage Report (Local Test Mode)", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    total_requests = random.randint(100, 1000)
    for label, val in [
        ("Period", f"Last {days} days"), ("Total Requests", f"{total_requests:,}"),
        ("Total Payload", f"{random.randint(10000, 100000):,} bytes"),
        ("Hours Active", f"{random.randint(10, 50)}"),
        ("Avg Requests/Hour", f"{total_requests // max(days * 24, 1):,}"),
    ]:
        table.add_row(label, val)
    f.console.print(table)
    f.console.print("\n[yellow]⚠ This is mock data. Set RAAS_LOCAL_TEST=false for real data.[/yellow]")
