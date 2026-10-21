# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Maintenance CLI Command - Phase 6

Interfaces with RaaS Gateway at api.cashclaw.cc to perform maintenance operations.
"""

from datetime import datetime, timezone
import json
import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.raas_maintenance_deep_check import (
    _display_deep_check_summary,
    _run_deep_checks,
)
from src.commands.raas_maintenance_display import (
    _clear_entitlements_cache,
    _clear_rate_limit_cache,
    _display_health_table,
    _display_status_table,
    _output_result,
    _reset_rate_limit,
)
from src.commands.raas_maintenance_ops import (
    cache_clear,
    health_check,
    maintenance_status,
    rate_limit_reset,
)
from src.raas.sync_client import SyncClient

console = Console()

app = typer.Typer(
    name="raas-maintenance",
    help="🔧 RaaS Gateway maintenance operations",
    rich_markup_mode="rich",
)

app.command("cache-clear")(cache_clear)
app.command("rate-limit-reset")(rate_limit_reset)
app.command("health")(health_check)
app.command("status")(maintenance_status)


@app.command("deep-check")
def deep_health_check(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output structured JSON logs"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Write results to file path"),
) -> None:
    """🔍 Deep health check of entire RaaS infrastructure."""
    result = {
        "command": "deep-check",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gateway_url": "https://api.cashclaw.cc",
        "success": False,
        "exit_code": 0,
        "checks": {
            "connectivity": {"status": "pending", "error": None},
            "authentication": {"status": "pending", "error": None, "details": None},
            "license_status": {"status": "pending", "error": None, "details": None},
            "webhook_delivery": {"status": "pending", "error": None, "details": None},
            "kv_usage_metering": {"status": "pending", "error": None, "details": None},
            "analytics_pipeline": {"status": "pending", "error": None, "details": None},
        },
        "summary": {},
        "errors": [],
    }

    all_passed = _run_deep_checks(result)

    passed = sum(1 for c in result["checks"].values() if c["status"] == "pass")
    failed = sum(1 for c in result["checks"].values() if c["status"] == "fail")
    warned = sum(1 for c in result["checks"].values() if c["status"] == "warn")

    result["summary"] = {
        "total_checks": len(result["checks"]),
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "health_score": f"{int((passed / len(result['checks'])) * 100)}%",
    }
    result["success"] = all_passed and failed == 0
    result["exit_code"] = 0 if result["success"] else 1

    for check_name, check_data in result["checks"].items():
        if check_data.get("error"):
            result["errors"].append({"check": check_name, "error": check_data["error"]})

    output_text = json.dumps(result, indent=2, default=str)
    if output_path:
        with open(output_path, "w") as f:
            f.write(output_text)
        console.print(f"[dim]Results written to: {output_path}[/dim]\n")

    if json_output:
        print(output_text)
    else:
        _display_deep_check_summary(result)

    if result["exit_code"] != 0:
        sys.exit(result["exit_code"])


if not hasattr(SyncClient, "_clear_rate_limit_cache"):
    SyncClient._clear_rate_limit_cache = _clear_rate_limit_cache
    SyncClient._clear_entitlements_cache = _clear_entitlements_cache
    SyncClient._reset_rate_limit = _reset_rate_limit

__all__ = [
    "Panel",
    "SyncClient",
    "Table",
    "_clear_entitlements_cache",
    "_clear_rate_limit_cache",
    "_display_deep_check_summary",
    "_display_health_table",
    "_display_status_table",
    "_output_result",
    "_reset_rate_limit",
    "app",
    "cache_clear",
    "console",
    "deep_health_check",
    "health_check",
    "maintenance_status",
    "rate_limit_reset",
]
