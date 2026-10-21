# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing Typer app instance, overview callback, and console formatting helpers."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from src.billing.engine import BillingResult

console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="billing",
    help="💰 Billing operations: usage submission, reconciliation, events",
    no_args_is_help=False,
)


def _mod() -> Any:
    return sys.modules.get("src.cli.billing_commands", sys.modules[__name__])


@app.callback(invoke_without_command=True)
def billing_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON billing overview",
    ),
) -> None:
    """💰 Billing Overview: Pricing tiers, active quotas, and engine status."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.billing_engine import get_billing_engine

    engine = get_billing_engine()
    status = engine.get_engine_status()
    tiers = engine.get_pricing_tiers()
    lic_status = engine.get_billing_status("mekong_lic_default")

    if json_output:
        overview = {
            **status,
            "tiers": tiers,
            "default_license_status": lic_status,
        }
        print(json.dumps(overview, indent=2))
        return

    from rich.box import ROUNDED
    from rich.panel import Panel

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"💳 [bold]Pricing Tiers:[/bold] [bold green]{status['pricing_tiers_count']}[/bold green]",
        f"📊 [bold]Events Recorded:[/bold] [bold cyan]{status['total_events_recorded']}[/bold cyan]",
    )
    grid.add_row(
        f"🧾 [bold]Invoices Simulated:[/bold] [bold yellow]{status['total_invoices_generated']}[/bold yellow]",
        f"🔍 [bold]Reconciliations Run:[/bold] [bold magenta]{status['total_reconciliations_run']}[/bold magenta]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]💰 Mekong Autonomous Billing Engine[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']} | Rate: 1 USD = {status['exchange_rate_vnd_per_usd']:,} VND[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    t_table = Table(
        title="🏷️ Available Monetization & Pricing Tiers",
        box=ROUNDED,
        header_style="bold yellow",
    )
    t_table.add_column("Tier Key", style="bold")
    t_table.add_column("Tier Name")
    t_table.add_column("Base Monthly", justify="right")
    t_table.add_column("Included MCU", justify="right")
    t_table.add_column("LLM Token Rate", justify="right")
    t_table.add_column("Agent Min Rate", justify="right")

    for k, v in tiers.items():
        t_table.add_row(
            k.upper(),
            v["name"],
            f"${v['base_monthly_usd']:.2f}",
            f"{v['included_mcu']:,}",
            f"${v['rates']['llm_tokens']:.4f}/k",
            f"${v['rates']['agent_minutes']:.3f}/min",
        )
    console.print(t_table)


def print_billing_result(result: BillingResult) -> None:
    """Print billing result to console."""
    console.print("\n[bold green]✓ Billing Calculation Complete[/bold green]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value")

    table.add_row("License Key", result.license_key)
    table.add_row("Period", f"{result.period_start.date()} → {result.period_end.date()}")
    table.add_row("Line Items", str(len(result.line_items)))
    table.add_row("Subtotal", f"${result.subtotal}")
    table.add_row("Discount", f"${result.discount}")
    table.add_row("Total", f"[bold green]${result.total}[/bold green]")
    table.add_row("Currency", result.currency)

    console.print(table)

    if result.line_items:
        console.print("\n[bold]Line Items:[/bold]")
        item_table = Table(show_header=True, header_style="bold yellow")
        item_table.add_column("Event Type")
        item_table.add_column("Model")
        item_table.add_column("Quantity")
        item_table.add_column("Unit")
        item_table.add_column("Unit Price")
        item_table.add_column("Amount")

        for item in result.line_items:
            item_table.add_row(
                item.event_type,
                item.model_name or "-",
                str(item.quantity),
                item.unit,
                f"${item.unit_price}",
                f"${item.final_amount}",
            )
        console.print(item_table)


def print_error(message: str, details: Optional[str] = None) -> None:
    """Print error message."""
    console.print(f"[bold red]✗ Error:[/bold red] {message}")
    if details:
        console.print(f"[dim]{details}[/dim]")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")
