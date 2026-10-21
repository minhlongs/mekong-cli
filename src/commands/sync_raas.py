# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Gateway Synchronization Command — ROIaaS Phase 5
=====================================================

Command for integrating with the live RaaS Gateway at api.cashclaw.cc.
"""

import json
from pathlib import Path
import time
from typing import Dict, Optional

import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import typer

from src.commands.sync_raas_analytics import (
    _get_cache,
    _save_cache,
    display_analytics,
    fetch_analytics,
)
from src.commands.sync_raas_client import (
    get_cli_version,
    get_license_key,
    register_cli_instance,
    track_usage,
    validate_license,
)

console = Console()
app = typer.Typer()

RAAS_GATEWAY_BASE_URL = "https://api.cashclaw.cc"
AUTH_ENDPOINT = f"{RAAS_GATEWAY_BASE_URL}/auth/validate"
REGISTER_ENDPOINT = f"{RAAS_GATEWAY_BASE_URL}/license/register"
USAGE_ENDPOINT = f"{RAAS_GATEWAY_BASE_URL}/usage"
ANALYTICS_ENDPOINT = f"{RAAS_GATEWAY_BASE_URL}/analytics/dashboard"

RATE_LIMIT_DELAY = 1.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0

CACHE_DIR = Path.home() / ".mekong" / "cache"
CACHE_FILE = CACHE_DIR / "raas_analytics_cache.json"
CACHE_TTL = 300


@app.command()
def sync(
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="Project ID for tracking"),
    force: bool = typer.Option(False, "--force", "-f", help="Force synchronization"),
    no_cache: bool = typer.Option(False, "--no-cache", "-n", help="Bypass local cache and fetch fresh data"),
) -> None:
    """Synchronize with RaaS Gateway at api.cashclaw.cc."""
    console.print(
        Panel(
            "[bold blue]🚀 Starting RaaS Gateway Synchronization[/bold blue]\n\n"
            "This process will validate your license, register your CLI instance,\n"
            "and fetch real-time analytics from the RaaS Gateway.",
            title="RaaS Synchronization",
            border_style="blue",
        )
    )

    license_key = get_license_key()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Validating license key...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        is_valid = validate_license(license_key)
        progress.update(task, completed=1)

    if not is_valid:
        raise typer.Exit(code=1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Registering CLI instance...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        is_registered = register_cli_instance(license_key)
        progress.update(task, completed=1)

    if not is_registered and not force:
        raise typer.Exit(code=1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Tracking usage...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        track_usage(license_key, "sync-raas", project_id)
        progress.update(task, completed=1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Fetching analytics...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        analytics_data = fetch_analytics(license_key, use_cache=not no_cache)
        progress.update(task, completed=1)

    if analytics_data:
        display_analytics(analytics_data)

    console.print(
        Panel(
            "[bold green]✅ RaaS Gateway synchronization complete[/bold green]\n\n"
            "Your CLI is now connected to the live RaaS Gateway.\n"
            "Usage data is being tracked and analytics are available.",
            title="✅ Synchronization Complete",
            border_style="green",
        )
    )


@app.command()
def validate_only() -> None:
    """Only validate the license key without other operations."""
    console.print(
        Panel(
            "[bold blue]🔑 License Validation Only[/bold blue]\n\n"
            "This will only validate your RAAS_LICENSE_KEY.",
            title="License Validation",
            border_style="blue",
        )
    )

    license_key = get_license_key()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Validating license key...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        is_valid = validate_license(license_key)
        progress.update(task, completed=1)

    if not is_valid:
        raise typer.Exit(code=1)


@app.command()
def analytics(
    no_cache: bool = typer.Option(False, "--no-cache", "-n", help="Bypass local cache and fetch fresh data"),
) -> None:
    """Only fetch and display real-time analytics."""
    console.print(
        Panel(
            "[bold blue]📊 Real-Time Analytics[/bold blue]\n\n"
            "This will fetch and display your RaaS usage analytics.",
            title="Analytics",
            border_style="blue",
        )
    )

    license_key = get_license_key()

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Fetching analytics...", total=1)
        time.sleep(RATE_LIMIT_DELAY)
        analytics_data = fetch_analytics(license_key, use_cache=not no_cache)
        progress.update(task, completed=1)

    if analytics_data:
        display_analytics(analytics_data)
    else:
        raise typer.Exit(code=1)


__all__ = [
    "ANALYTICS_ENDPOINT", "AUTH_ENDPOINT", "CACHE_DIR", "CACHE_FILE", "CACHE_TTL",
    "Dict", "MAX_RETRIES", "RAAS_GATEWAY_BASE_URL", "RATE_LIMIT_DELAY",
    "REGISTER_ENDPOINT", "RETRY_DELAY", "Table", "USAGE_ENDPOINT",
    "_get_cache", "_save_cache", "analytics", "app", "console",
    "display_analytics", "fetch_analytics", "get_cli_version", "get_license_key",
    "json", "register_cli_instance", "requests", "sync", "track_usage",
    "validate_license", "validate_only",
]
