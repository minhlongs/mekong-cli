# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
OCOP Commands for Mekong CLI

One Commune One Product — AI-powered agricultural export platform.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import typer

from src.commands.ocop_ai_helpers import (
    _display_analysis,
    _display_listing,
    _generate_analysis,
    _generate_fallback_analysis,
    _generate_fallback_listing,
    _generate_listing,
)
from src.commands.ocop_engine_commands import (
    ocop_eval,
    ocop_main,
    ocop_products,
)
from src.commands.ocop_export_commands import (
    analyze,
    ocop_compliance,
    ocop_listing,
    ocop_status,
)
from src.providers.llm.client import get_client

console = Console()
app = typer.Typer(help="OCOP: AI-powered agricultural export tools & star rating", add_completion=False)

app.callback(invoke_without_command=True)(ocop_main)
app.command(name="eval")(ocop_eval)
app.command(name="products")(ocop_products)
app.command(name="listing")(ocop_listing)
app.command(name="compliance")(ocop_compliance)
app.command(name="status")(ocop_status)
app.command("analyze")(analyze)


@app.command("export")
def export_listing(
    target: str = typer.Option(..., "--target", "-t", help="Target platform (amazon, alibaba, shopee, lazada, tiki)"),
    product_file: str = typer.Option(None, "--product", "-p", help="Product analysis JSON (from 'ocop analyze')"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview listing without submitting"),
):
    """Generate B2B export listings from analyzed product data."""
    valid_targets = ["amazon", "alibaba", "shopee", "lazada", "tiki", "grab", "sendo"]
    if target.lower() not in valid_targets:
        console.print(f"[red]Error: Unknown target '{target}'[/red]")
        console.print(f"[dim]Available: {', '.join(valid_targets)}[/dim]")
        raise typer.Exit(1)

    console.print(
        Panel(
            f"[bold cyan]Target:[/bold cyan] {target.upper()}\n"
            f"[bold cyan]Mode:[/bold cyan] {'Preview' if dry_run else 'Live'}",
            title="📦 OCOP Export Generator",
            border_style="green",
        )
    )

    product_data = None
    if product_file:
        pf = Path(product_file)
        if not pf.exists():
            console.print(f"[red]Error: Product file not found: {product_file}[/red]")
            raise typer.Exit(1)
        try:
            product_data = json.loads(pf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON — {e}[/red]")
            raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(f"Generating {target} listing...", total=None)
        listing = _generate_listing(target, product_data)
        progress.update(task, description="Listing generated!")

    _display_listing(listing, target, dry_run)
    if dry_run:
        console.print("\n[yellow]Dry run — listing not submitted[/yellow]")
    else:
        console.print(f"\n[green]✓ Listing ready for {target.upper()}[/green]")


@app.command("list")
def list_platforms():
    """Show available export platforms and their status."""
    console.print(Panel("Supported Export Platforms", title="🌍 OCOP Platforms", border_style="green"))

    table = Table(show_header=True)
    table.add_column("Platform", style="cyan")
    table.add_column("Region", style="dim")
    table.add_column("Status", style="green")
    table.add_column("API")

    platforms = [
        ("Amazon", "Global", "Ready", "REST"),
        ("Alibaba", "China / Global", "Ready", "REST"),
        ("Shopee", "Southeast Asia", "Ready", "REST"),
        ("Lazada", "Southeast Asia", "Ready", "REST"),
        ("Tiki", "Vietnam", "Ready", "REST"),
        ("Grab", "Southeast Asia", "Beta", "gRPC"),
        ("Sendo", "Vietnam", "Beta", "REST"),
    ]

    for name, region, status, api in platforms:
        status_styled = f"[green]{status}[/green]" if status == "Ready" else f"[yellow]{status}[/yellow]"
        table.add_row(name, region, status_styled, api)

    console.print(table)


__all__ = [
    "Optional",
    "_display_analysis",
    "_display_listing",
    "_generate_analysis",
    "_generate_fallback_analysis",
    "_generate_fallback_listing",
    "_generate_listing",
    "analyze",
    "app",
    "console",
    "export_listing",
    "get_client",
    "list_platforms",
    "ocop_compliance",
    "ocop_eval",
    "ocop_listing",
    "ocop_main",
    "ocop_products",
    "ocop_status",
]
