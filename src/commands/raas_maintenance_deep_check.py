# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Deep health check for RaaS Maintenance CLI."""

import sys

from rich.panel import Panel
from rich.table import Table


def _facade():
    return sys.modules["src.commands.raas_maintenance_commands"]


def _display_deep_check_summary(result: dict) -> None:
    """Display deep health check summary."""
    f = _facade()
    f.console.print("\n[bold cyan]🔍 RaaS Infrastructure Deep Health Check[/bold cyan]\n")

    status_color = "green" if result["success"] else "red"
    status_icon = "✅" if result["success"] else "❌"
    f.console.print(Panel(
        f"[bold {status_color}]{status_icon} Overall Health: {result['summary']['health_score']}[/bold {status_color}]\n"
        f"Passed: [green]{result['summary']['passed']}[/green] | "
        f"Failed: [red]{result['summary']['failed']}[/red] | "
        f"Warnings: [yellow]{result['summary']['warned']}[/yellow]",
        title="Deep Check Summary", border_style=status_color,
    ))
    f.console.print()

    table = Table(title="Check Results", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="dim", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details", style="white")
    check_icons = {"pass": "✅", "fail": "❌", "warn": "⚠️", "pending": "⏳"}

    for check_name, check_data in result["checks"].items():
        status = check_data.get("status", "unknown")
        icon = check_icons.get(status, "❓")
        st_color = {"pass": "green", "fail": "red", "warn": "yellow", "pending": "dim"}.get(status, "white")
        details_data = check_data.get("details")
        if isinstance(details_data, dict):
            details = [f"{k}: {v}" for k, v in details_data.items() if v is not None]
        else:
            details = [str(details_data)] if details_data else []
        if check_data.get("error"):
            details.append(f"[dim]{check_data['error']}[/dim]")
        table.add_row(check_name.replace("_", " ").title(), f"[{st_color}]{icon} {status}[/{st_color}]", " | ".join(details) if details else "-")

    f.console.print(table)
    if result["errors"]:
        f.console.print("\n[bold red]⚠️ Errors Detected:[/bold red]\n")
        for err in result["errors"]:
            f.console.print(f"  • [red]{err['check']}[/red]: {err['error']}")
    f.console.print()


def _run_deep_checks(result: dict) -> bool:
    """Execute the 6 deep infrastructure checks and populate result['checks']."""
    from src.core.gateway_client import GatewayClient
    from src.core.kv_store_client import get_kv_client
    from src.core.raas_auth import get_auth_client
    from src.raas.sync_client import get_sync_client

    f = _facade()
    all_passed = True

    try:
        health = GatewayClient().get_health_status()
        if health.get("status") == "healthy":
            result["checks"]["connectivity"].update(
                status="pass", details={"latency_ms": health.get("latency_ms"), "gateway_version": health.get("version")}
            )
        else:
            result["checks"]["connectivity"].update(status="fail", error="Gateway unhealthy")
            all_passed = False
    except Exception as e:
        result["checks"]["connectivity"].update(status="fail", error=str(e))
        all_passed = False

    try:
        auth_client = get_auth_client()
        session = auth_client.get_session()
        if not session.authenticated:
            api_key = f.os.getenv("RAAS_LICENSE_KEY")
            if api_key:
                val = auth_client.validate_credentials(api_key)
                if val.valid:
                    result["checks"]["authentication"].update(status="pass", details={"auth_type": "api_key", "tenant_id": val.tenant_id})
                else:
                    result["checks"]["authentication"].update(status="fail", error=val.error)
                    all_passed = False
            else:
                result["checks"]["authentication"].update(status="fail", error="No API key or session")
                all_passed = False
        else:
            result["checks"]["authentication"].update(
                status="pass",
                details={
                    "auth_type": "jwt_session",
                    "tenant_id": session.tenant.tenant_id if session.tenant else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                },
            )
    except Exception as e:
        result["checks"]["authentication"].update(status="fail", error=str(e))
        all_passed = False

    try:
        ent = get_sync_client().fetch_entitlements()
        if "error" not in ent and ent.get("tenant_id"):
            result["checks"]["license_status"].update(
                status="pass", details={k: ent.get(k) for k in ("tenant_id", "tier", "features", "rate_limit", "expires_at")}
            )
        else:
            result["checks"]["license_status"].update(status="fail", error=ent.get("error", "Invalid license"))
            all_passed = False
    except Exception as e:
        result["checks"]["license_status"].update(status="fail", error=str(e))
        all_passed = False

    try:
        wh = get_sync_client().get_webhook_status()
        result["checks"]["webhook_delivery"].update(
            status="pass" if wh.get("configured") else "warn",
            details=wh if wh.get("configured") else None,
            error=None if wh.get("configured") else "Webhook not configured",
        )
    except Exception as e:
        result["checks"]["webhook_delivery"].update(status="fail", error=str(e))

    try:
        kv_client = get_kv_client()
        kv_state, usage_state = kv_client.get_rate_limit_state(), kv_client.get_usage_state()
        if kv_state and usage_state:
            result["checks"]["kv_usage_metering"].update(
                status="pass",
                details={
                    "rate_limit_remaining": kv_state.remaining, "rate_limit_limit": kv_state.limit,
                    "usage_events_cached": usage_state.cached_count, "last_sync": usage_state.last_sync,
                },
            )
        else:
            result["checks"]["kv_usage_metering"].update(status="warn", error="KV state incomplete")
    except Exception as e:
        result["checks"]["kv_usage_metering"].update(status="fail", error=str(e))

    try:
        an = get_sync_client().get_analytics_status()
        if an.get("healthy"):
            result["checks"]["analytics_pipeline"].update(
                status="pass", details={k: an.get(k) for k in ("dashboard_url", "last_push", "events_pushed")}
            )
        else:
            result["checks"]["analytics_pipeline"].update(status="warn", error=an.get("error", "Analytics not configured"))
    except Exception as e:
        result["checks"]["analytics_pipeline"].update(status="fail", error=str(e))

    return all_passed
