# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Display and SyncClient helpers for RaaS Maintenance CLI."""

import json
import os
import sys

from rich.panel import Panel
from rich.table import Table


def _facade():
    return sys.modules["src.commands.raas_maintenance_commands"]


def _output_result(result: dict, as_json: bool) -> None:
    """Output result as JSON or rich console."""
    f = _facade()
    if as_json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result.get("success"):
            f.console.print(Panel(
                f"[green]✓ {result.get('message', 'Success')}[/green]\n"
                f"[dim]Command: {result.get('command')}[/dim]",
                title="✅ Success",
                border_style="green",
            ))
        else:
            f.console.print(Panel(
                f"[red]✗ {result.get('error', 'Failed')}[/red]",
                title="❌ Error",
                border_style="red",
            ))


def _display_health_table(health_status: dict, verbose: bool) -> None:
    """Display health check results in table."""
    f = _facade()
    status = health_status.get("status", "unknown")
    status_color = "green" if status == "healthy" else "yellow" if status == "degraded" else "red"

    f.console.print(f"\n[bold {status_color}]RaaS Gateway Health: {status.upper()}[/{status_color}]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Check", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    checks = health_status.get("checks", {})
    for check_name, check_data in checks.items():
        check_status = check_data.get("status", "unknown")
        check_color = "green" if check_status == "ok" else "red"
        table.add_row(
            check_name,
            f"[{check_color}]{check_status}[/{check_color}]",
            check_data.get("message", ""),
        )

    f.console.print(table)

    if verbose:
        f.console.print(f"\n[dim]Latency: {health_status.get('latency_ms', 0):.0f}ms[/dim]")
        f.console.print(f"[dim]Gateway: {health_status.get('gateway_url', 'N/A')}[/dim]\n")


def _display_status_table(result: dict) -> None:
    """Display maintenance status in table."""
    f = _facade()
    f.console.print("\n[bold]RaaS Maintenance Status[/bold]\n")

    gateway_table = Table(title="Gateway Status", show_header=False, box=None)
    gateway_table.add_column("Property", style="dim")
    gateway_table.add_column("Value", style="cyan")

    gateway = result.get("gateway", {})
    for key, value in gateway.items():
        gateway_table.add_row(key.replace("_", " ").title(), str(value))

    f.console.print(gateway_table)

    cache_table = Table(title="Cache Status", show_header=False, box=None)
    cache_table.add_column("Property", style="dim")
    cache_table.add_column("Value", style="cyan")

    cache = result.get("cache", {})
    cache_table.add_row("Metrics Count", str(cache.get("metrics_count", 0)))
    cache_table.add_row("Last Sync", str(cache.get("last_sync", "Never")))

    f.console.print(cache_table)

    rate_limits = result.get("rate_limits", {})
    if rate_limits:
        f.console.print("\n[bold]Rate Limit Circuit Breakers:[/bold]")
        for gateway_name, info in rate_limits.items():
            state = info.get("state", "unknown")
            state_color = {"closed": "green", "half-open": "yellow", "open": "red"}.get(state, "white")
            f.console.print(f"  {gateway_name}: [{state_color}]{state}[/{state_color}]")

    f.console.print()


def _clear_rate_limit_cache(self) -> bool:
    """Clear rate limit cache."""
    try:
        from src.core.kv_store_client import get_kv_client
        kv_client = get_kv_client()
        kv_client.clear_rate_limit_state()
        return True
    except Exception:
        return False


def _clear_entitlements_cache(self) -> bool:
    """Clear entitlements cache."""
    try:
        self._entitlements_cache = None
        return True
    except Exception:
        return False


def _reset_rate_limit(self, org_id: str, force: bool = False) -> dict:
    """Reset rate limit for organization."""
    try:
        license_key = os.getenv("RAAS_LICENSE_KEY", "")
        response = self.gateway.post(
            "/v1/admin/rate-limit/reset",
            json={"org_id": org_id, "force": force},
            headers={"Authorization": f"Bearer {license_key}"},
        )
        return {
            "success": True,
            "rate_limit": response.data.get("rate_limit"),
            "message": "Rate limit reset successfully",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
