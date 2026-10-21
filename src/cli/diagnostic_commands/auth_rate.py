# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth and rate-limit diagnostic commands."""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from src.cli.diagnostic_commands.gateway import app, console


@app.command("auth")
def check_auth(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Token to test (defaults to stored credentials)"),
    gateway_url: Optional[str] = typer.Option(None, "--gateway", "-g", help="Gateway URL to test against"),
) -> None:
    """🔐 Test credential validation against RaaS Gateway."""
    from src.core.raas_auth import RaaSAuthClient

    console.print("[bold cyan]🔐 Credential Validation Test[/bold cyan]\n")
    client = RaaSAuthClient(gateway_url=gateway_url)

    if not token:
        session = client.get_session()
        token = session.token if session.authenticated else os.getenv("RAAS_LICENSE_KEY")

    if not token:
        console.print("[yellow]No credentials found.[/yellow]")
        console.print("Set RAAS_LICENSE_KEY env var or login: [bold]mekong auth login[/bold]\n")
        return

    console.print(f"Testing token: [cyan]{token[:8]}...{token[-4:] if len(token) > 4 else ''}[/cyan]\n")
    start_time = time.time()
    result = client.validate_credentials(token)
    elapsed_ms = (time.time() - start_time) * 1000

    table = Table(title="Validation Result", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value")
    table.add_row("Status", "[green]✅ Valid[/green]" if result.valid else "[red]❌ Invalid[/red]")
    table.add_row("Response Time", f"{elapsed_ms:.1f} ms")

    if result.valid and result.tenant:
        table.add_row("Tenant ID", result.tenant.tenant_id)
        table.add_row("Tier", result.tenant.tier.upper())
        table.add_row("Role", result.tenant.role)
        if result.tenant.features:
            table.add_row("Features", f"{len(result.tenant.features)} enabled")
        console.print(table)
        console.print(Panel(f"[bold green]✅ Credentials are valid![/bold green]\nGateway: {client.gateway_url}", title="Auth Status", border_style="green"))
    else:
        console.print(table)
        console.print(Panel(f"[bold red]❌ Validation Failed[/bold red]\nError: {result.error}\nCode: {result.error_code}", title="Auth Status", border_style="red"))


@app.command("rate-limit")
def check_rate_limit(
    gateway_url: Optional[str] = typer.Option(None, "--gateway", "-g", help="Gateway URL to test"),
    num_requests: int = typer.Option(5, "--requests", "-n", help="Number of requests to send"),
) -> None:
    """🚦 Test rate limit enforcement."""
    if num_requests < 1:
        console.print("[red]Error: --requests must be at least 1[/red]\n")
        raise typer.Exit(1)
    if num_requests > 20:
        console.print("[red]Error: --requests cannot exceed 20[/red]\n")
        raise typer.Exit(1)

    import requests

    from src.core.gateway_client import GATEWAY_URLS
    from src.core.raas_auth import RaaSAuthClient

    console.print("[bold cyan]🚦 Rate Limit Enforcement Test[/bold cyan]\n")
    url = gateway_url or GATEWAY_URLS[0] or "https://api.cashclaw.cc"
    test_endpoint = f"{url}/health"
    console.print(f"Testing: [cyan]{test_endpoint}[/cyan]\nRequests: [cyan]{num_requests}[/cyan]\n")

    client = RaaSAuthClient(gateway_url=url)
    session = client.get_session()
    headers: dict[str, str] = {}
    tok = session.token if session.authenticated else os.getenv("RAAS_LICENSE_KEY")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    results: list[dict[str, Any]] = []
    rate_limit_headers: dict[str, Any] = {}

    for i in range(num_requests):
        try:
            start = time.time()
            response = requests.get(test_endpoint, headers=headers, timeout=10)
            elapsed = (time.time() - start) * 1000
            results.append({
                "request": i + 1,
                "status": response.status_code,
                "time_ms": elapsed,
                "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                "rate_limit_limit": response.headers.get("X-RateLimit-Limit"),
                "rate_limit_reset": response.headers.get("X-RateLimit-Reset"),
                "retry_after": response.headers.get("Retry-After"),
            })
            rate_limit_headers = {
                "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
                "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
            }
        except Exception as e:
            results.append({"request": i + 1, "status": "ERROR", "time_ms": None, "error": str(e)})

    table = Table(title="Rate Limit Test Results", show_header=True, header_style="bold cyan")
    for col, just in [("#", "right"), ("Status", "center"), ("Time (ms)", "right"), ("Remaining", "right"), ("Limit", "right")]:
        table.add_column(col, justify=just)  # type: ignore[arg-type]

    for result in results:
        st = str(result["status"])
        st_disp = f"[green]{st}[/green]" if st == "200" else f"[yellow]{st}[/yellow]" if st == "429" else f"[red]{st}[/red]" if st == "ERROR" else st
        table.add_row(
            str(result["request"]), st_disp,
            f"{result['time_ms']:.1f}" if result.get("time_ms") else "-",
            str(result.get("rate_limit_remaining", "-")),
            str(result.get("rate_limit_limit", "-")),
        )
    console.print(table)

    if rate_limit_headers.get("X-RateLimit-Limit"):
        console.print("\n[bold]Rate Limit Configuration:[/bold]")
        rate_table = Table(show_header=False, box=None)
        rate_table.add_column("Header", style="dim")
        rate_table.add_column("Value", style="cyan")
        for header, value in rate_limit_headers.items():
            if value:
                rate_table.add_row(header, value)
        console.print(rate_table)

        remaining = int(rate_limit_headers.get("X-RateLimit-Remaining", 0) or 0)
        limit = int(rate_limit_headers.get("X-RateLimit-Limit", 0) or 0)
        if remaining == 0:
            console.print(Panel(f"[bold red]🛑 Rate limit EXHAUSTED![/bold red]\nWait until reset: {rate_limit_headers.get('X-RateLimit-Reset', 'unknown')}", title="Rate Limit Status", border_style="red"))
        elif remaining < limit * 0.2:
            console.print(Panel(f"[bold yellow]⚠️ Rate limit nearly exhausted[/bold yellow]\n{remaining}/{limit} requests remaining", title="Rate Limit Status", border_style="yellow"))
        else:
            console.print(Panel(f"[bold green]✅ Rate limit healthy[/bold green]\n{remaining}/{limit} requests remaining", title="Rate Limit Status", border_style="green"))
