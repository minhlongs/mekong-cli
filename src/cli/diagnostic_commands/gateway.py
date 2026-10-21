# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway connectivity diagnostic command."""

from __future__ import annotations

import sys
import time
from typing import Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(
    name="diagnostic",
    help="🔍 Diagnostic connectivity checks",
    rich_markup_mode="rich",
)


def _mod() -> Any:
    return sys.modules.get("src.cli.diagnostic_commands", sys.modules[__name__])


@app.command("gateway")
def check_gateway(
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help="Gateway URL to test (default: from env)",
    ),
    timeout: int = typer.Option(
        10,
        "--timeout",
        "-t",
        help="Request timeout in seconds",
    ),
) -> None:
    """
    🌐 Check RaaS Gateway connectivity.

    Tests:
      - DNS resolution
      - HTTPS handshake
      - Health endpoint response
      - Response time measurement

    Examples:
        mekong diagnostic gateway
        mekong diagnostic gateway -u https://api.cashclaw.cc
        mekong diagnostic gateway -t 5
    """
    import requests

    from src.core.gateway_client import GATEWAY_URLS

    console.print("[bold cyan]🌐 RaaS Gateway Connectivity Test[/bold cyan]\n")

    gateway_url = url or GATEWAY_URLS[0] or "https://api.cashclaw.cc"
    console.print(f"Testing: [cyan]{gateway_url}[/cyan]\n")

    results: dict[str, dict[str, Any]] = {
        "dns_resolution": {"status": "pending", "time_ms": None, "error": None},
        "https_handshake": {"status": "pending", "time_ms": None, "error": None},
        "health_endpoint": {"status": "pending", "time_ms": None, "error": None},
        "response_headers": {"status": "pending", "headers": {}},
    }

    start_time = time.time()
    try:
        requests.head(gateway_url, timeout=timeout, allow_redirects=True)
        elapsed_ms = (time.time() - start_time) * 1000

        results["dns_resolution"]["status"] = "✅"
        results["dns_resolution"]["time_ms"] = elapsed_ms
        results["https_handshake"]["status"] = "✅"
        results["https_handshake"]["time_ms"] = elapsed_ms

        health_url = f"{gateway_url}/health"
        health_start = time.time()
        try:
            health_response = requests.get(health_url, timeout=timeout)
            health_elapsed = (time.time() - health_start) * 1000

            if health_response.status_code == 200:
                results["health_endpoint"]["status"] = "✅"
                results["health_endpoint"]["time_ms"] = health_elapsed
                results["health_endpoint"]["data"] = health_response.json()
            else:
                results["health_endpoint"]["status"] = "⚠️"
                results["health_endpoint"]["error"] = f"HTTP {health_response.status_code}"

            results["response_headers"]["headers"] = dict(health_response.headers)
        except requests.exceptions.Timeout:
            results["health_endpoint"]["status"] = "❌"
            results["health_endpoint"]["error"] = f"Timeout ({timeout}s)"
        except requests.exceptions.RequestException as e:
            results["health_endpoint"]["status"] = "❌"
            results["health_endpoint"]["error"] = str(e)

    except requests.exceptions.SSLError as e:
        results["https_handshake"]["status"] = "❌"
        results["https_handshake"]["error"] = f"SSL Error: {str(e)}"
        results["dns_resolution"]["status"] = "⚠️"
        results["dns_resolution"]["error"] = "DNS resolved, SSL failed"
    except requests.exceptions.Timeout:
        results["dns_resolution"]["status"] = "❌"
        results["dns_resolution"]["error"] = f"Timeout ({timeout}s)"
    except requests.exceptions.ConnectionError as e:
        results["dns_resolution"]["status"] = "❌"
        results["dns_resolution"]["error"] = f"Connection failed: {str(e)}"
    except Exception as e:
        results["dns_resolution"]["status"] = "❌"
        results["dns_resolution"]["error"] = str(e)

    table = Table(title="Gateway Connectivity Results", show_header=True, header_style="bold cyan")
    table.add_column("Test", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Time (ms)", justify="right")
    table.add_column("Details")

    for test_name, result in results.items():
        if test_name == "response_headers":
            continue
        status = result.get("status", "?")
        time_ms = result.get("time_ms")
        error = result.get("error", "")
        time_str = f"{time_ms:.1f}" if time_ms else "-"
        details = error if error else (result.get("data", {}) or "OK")
        table.add_row(test_name.replace("_", " ").title(), status, time_str, str(details)[:50])

    console.print(table)

    headers = results["response_headers"].get("headers", {})
    rate_limit_headers = {
        k: v for k, v in headers.items()
        if k.lower().startswith("x-ratelimit") or k.lower() == "retry-after"
    }

    if rate_limit_headers:
        console.print("\n[bold]Rate Limit Headers:[/bold]")
        rate_table = Table(show_header=False, box=None)
        rate_table.add_column("Header", style="dim")
        rate_table.add_column("Value", style="green")
        for header, value in rate_limit_headers.items():
            rate_table.add_row(header, value)
        console.print(rate_table)

    all_passed = all(
        results[test]["status"] == "✅"
        for test in ["dns_resolution", "https_handshake", "health_endpoint"]
    )
    if all_passed:
        console.print(
            Panel(
                "[bold green]✅ Gateway is healthy and reachable![/bold green]",
                title="Overall Status",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ Gateway connectivity issues detected[/bold red]",
                title="Overall Status",
                border_style="red",
            )
        )
