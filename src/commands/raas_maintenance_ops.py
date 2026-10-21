# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Operational commands for RaaS Maintenance CLI."""

from datetime import datetime, timezone
import sys

import typer


def _facade():
    return sys.modules["src.commands.raas_maintenance_commands"]


def cache_clear(
    cache_type: str = typer.Option("all", "--type", "-t", help="Cache type to clear: all, rate-limits, entitlements, sessions"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be cleared without sending"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output structured JSON logs"),
) -> None:
    """🗑️ Clear cached data from RaaS Gateway."""
    from src.core.raas_auth import get_auth_client
    from src.raas.sync_client import get_sync_client

    f = _facade()
    result = {
        "command": "cache-clear", "timestamp": datetime.now(timezone.utc).isoformat(),
        "cache_type": cache_type, "dry_run": dry_run, "success": False, "cleared": [], "error": None,
    }
    auth_client = get_auth_client()
    session = auth_client.get_session()

    if not session.authenticated and not f.os.getenv("RAAS_LICENSE_KEY"):
        result["error"] = "Not authenticated. Set RAAS_LICENSE_KEY or run 'mekong raas-auth login'"
        f._output_result(result, json_output)
        return

    if dry_run:
        result.update(dry_run=True, success=True, message=f"Would clear cache type: {cache_type}")
        f._output_result(result, json_output)
        return

    try:
        client = get_sync_client()
        cleared = []
        if cache_type in ("all", "rate-limits") and client._clear_rate_limit_cache():
            cleared.append("rate-limits")
        if cache_type in ("all", "entitlements") and client._clear_entitlements_cache():
            cleared.append("entitlements")
        if cache_type in ("all", "sessions") and auth_client.clear_session_cache():
            cleared.append("sessions")

        result.update(success=len(cleared) > 0, cleared=cleared, message=f"Cleared {len(cleared)} cache type(s)")
    except Exception as e:
        result["error"] = str(e)

    f._output_result(result, json_output)


def rate_limit_reset(
    org_id: str = typer.Argument(..., help="Organization ID to reset rate limit for"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reset even if recently reset"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output structured JSON logs"),
) -> None:
    """🔄 Reset rate limit for an organization."""
    from src.raas.sync_client import get_sync_client

    f = _facade()
    result = {
        "command": "rate-limit-reset", "timestamp": datetime.now(timezone.utc).isoformat(),
        "org_id": org_id, "force": force, "success": False, "rate_limit": None, "error": None,
    }
    if not f.os.getenv("RAAS_LICENSE_KEY"):
        result["error"] = "RAAS_LICENSE_KEY not set"
        f._output_result(result, json_output)
        return

    try:
        response = get_sync_client()._reset_rate_limit(org_id, force=force)
        result.update(
            success=response.get("success", False), rate_limit=response.get("rate_limit"),
            message=response.get("message", "Rate limit reset successfully"),
        )
    except Exception as e:
        result["error"] = str(e)

    f._output_result(result, json_output)


def health_check(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output structured JSON logs"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed health information"),
) -> None:
    """🏥 Check RaaS Gateway health status."""
    from src.core.gateway_client import GatewayClient

    f = _facade()
    result = {
        "command": "health", "timestamp": datetime.now(timezone.utc).isoformat(),
        "gateway_url": "https://api.cashclaw.cc", "success": False, "status": "unknown", "checks": {}, "error": None,
    }
    try:
        health_status = GatewayClient().get_health_status()
        result.update(
            success=health_status.get("status") == "healthy", status=health_status.get("status", "unknown"),
            checks=health_status.get("checks", {}), latency_ms=health_status.get("latency_ms"),
        )
        if verbose:
            result["details"] = health_status
        if not json_output:
            f._display_health_table(health_status, verbose)
        else:
            f._output_result(result, json_output)
    except Exception as e:
        result.update(error=str(e), status="error")
        f._output_result(result, json_output)


def maintenance_status(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output structured JSON logs"),
) -> None:
    """📊 Show current maintenance status."""
    from src.core.gateway_client import GatewayClient
    from src.raas.sync_client import get_sync_client

    f = _facade()
    result = {
        "command": "status", "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": True, "gateway": {}, "cache": {}, "rate_limits": {}, "error": None,
    }
    try:
        result["gateway"] = GatewayClient().get_circuit_status()
        sync_status = get_sync_client().get_sync_status()
        result["cache"] = {"metrics_count": sync_status.get("metrics_count", 0), "last_sync": sync_status.get("last_sync")}
        result["rate_limits"] = sync_status.get("circuit_breakers", {})
        if not json_output:
            f._display_status_table(result)
        else:
            f._output_result(result, json_output)
    except Exception as e:
        result.update(error=str(e), success=False)
        f._output_result(result, json_output)
