# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Full diagnostic suite runner and internal impl helpers."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from src.cli.diagnostic_commands.auth_rate import check_auth, check_rate_limit
from src.cli.diagnostic_commands.gateway import _mod, app, check_gateway, console


def check_gateway_impl(url: Optional[str] = None, timeout: int = 10) -> None:
    """Internal implementation for reuse in 'all' command."""
    check_gateway(url=url, timeout=timeout)


def check_auth_impl(token: Optional[str] = None, gateway_url: Optional[str] = None) -> None:
    """Internal implementation for reuse in 'all' command."""
    check_auth(token=token, gateway_url=gateway_url)


def check_rate_limit_impl(
    gateway_url: Optional[str] = None,
    num_requests: int = 3,
) -> None:
    """Internal implementation for reuse in 'all' command."""
    check_rate_limit(gateway_url=gateway_url, num_requests=num_requests)


@app.command("all")
def run_all_diagnostics(
    gateway_url: Optional[str] = typer.Option(
        None,
        "--gateway",
        "-g",
        help="Gateway URL to test",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for JSON report",
    ),
) -> None:
    """
    📋 Run full diagnostic suite.

    Executes all diagnostic tests and generates a report.
    """
    mod = _mod()
    console.print("[bold cyan]📋 Full Diagnostic Suite[/bold cyan]\n")
    console.print("Running: Gateway → Auth → Rate Limit\n")
    console.print("=" * 60)

    results: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gateway_url": gateway_url,
        "tests": {},
        "overall_status": "healthy",
    }

    console.print("\n[bold]1/3: Gateway Connectivity[/bold]\n")
    try:
        mod.check_gateway_impl(gateway_url=gateway_url)
        results["tests"]["gateway"] = {"status": "passed"}
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}\n")
        results["tests"]["gateway"] = {"status": "failed", "error": str(e)}
        results["overall_status"] = "degraded"

    console.print("\n" + "=" * 60)

    console.print("\n[bold]2/3: Credential Validation[/bold]\n")
    try:
        mod.check_auth_impl(gateway_url=gateway_url)
        results["tests"]["auth"] = {"status": "passed"}
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}\n")
        results["tests"]["auth"] = {"status": "failed", "error": str(e)}
        results["overall_status"] = "degraded"

    console.print("\n" + "=" * 60)

    console.print("\n[bold]3/3: Rate Limit Enforcement[/bold]\n")
    try:
        mod.check_rate_limit_impl(gateway_url=gateway_url, num_requests=3)
        results["tests"]["rate_limit"] = {"status": "passed"}
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}\n")
        results["tests"]["rate_limit"] = {"status": "failed", "error": str(e)}
        results["overall_status"] = "degraded"

    console.print("\n" + "=" * 60)

    console.print("\n[bold]📊 Diagnostic Summary[/bold]\n")

    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Test", style="dim")
    summary_table.add_column("Status", justify="center")

    for test_name, test_result in results["tests"].items():
        status = "✅" if test_result["status"] == "passed" else "❌"
        summary_table.add_row(test_name.title(), status)

    console.print(summary_table)

    if results["overall_status"] == "healthy":
        console.print(
            Panel(
                "[bold green]✅ All diagnostics passed![/bold green]\n"
                "Your RaaS Gateway connection is healthy.",
                title="Overall Status",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold yellow]⚠️ Some diagnostics failed[/bold yellow]\n"
                "Review the results above for details.",
                title="Overall Status",
                border_style="yellow",
            )
        )

    if output:
        output_path = Path(output)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✓ Report exported to:[/green] {output_path}\n")
