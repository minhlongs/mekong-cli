# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rich rendering helpers for Revenue Operations CLI commands."""

from __future__ import annotations

from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render_revenue_dashboard(console: Console, metrics: dict[str, Any], status: dict[str, Any]) -> None:
    """Render the main revenue operations dashboard, waterfall, and tier breakdown."""
    mrr_str = f"[bold green]${metrics['mrr']:,.2f}[/bold green]"
    arr_str = f"[bold cyan]${metrics['arr']:,.2f}[/bold cyan]"
    total_rev = f"[bold white]${metrics['total_revenue']:,.2f}[/bold white]"
    paying_cust = f"[bold yellow]{metrics['paying_customers']}[/bold yellow]"
    arpu_str = f"[bold magenta]${metrics['arpu']:,.2f}[/bold magenta]"
    ltv_str = f"[bold blue]${metrics['ltv']:,.2f}[/bold blue]"
    nrr_str = f"[bold green]{metrics['nrr_pct']}%[/bold green]"

    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(
        f"💳 [bold]Monthly Recurring (MRR):[/bold] {mrr_str}",
        f"📈 [bold]Annual Recurring (ARR):[/bold] {arr_str}",
    )
    grid.add_row(
        f"🏦 [bold]Total Collected Revenue:[/bold] {total_rev}",
        f"👥 [bold]Active Paying Customers:[/bold] {paying_cust}",
    )
    grid.add_row(
        f"📊 [bold]Average Revenue / User (ARPU):[/bold] {arpu_str}",
        f"🎯 [bold]Customer Lifetime Value (LTV):[/bold] {ltv_str}",
    )
    grid.add_row(
        f"🔄 [bold]Net Revenue Retention (NRR):[/bold] {nrr_str}",
        f"📉 [bold]Churn Rate:[/bold] [dim]{metrics['churn_rate_pct']}%[/dim]",
    )

    console.print(
        Panel(
            grid,
            title="[bold green]💰 Mekong Revenue Operations Dashboard[/bold green]",
            subtitle=f"[dim]DB: {status['db_path']} | Engine: {status['status']}[/dim]",
            border_style="green",
            box=ROUNDED,
        )
    )

    wf = metrics["mrr_waterfall"]
    wf_table = Table(
        title="🌊 MRR Waterfall Breakdown",
        box=ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    wf_table.add_column("Component", style="bold")
    wf_table.add_column("Amount (USD)", justify="right")
    wf_table.add_column("Impact Description", style="dim")

    wf_table.add_row("New MRR", f"+${wf['new_mrr']:,.2f}", "New customer subscriptions")
    wf_table.add_row("Expansion MRR", f"+${wf['expansion_mrr']:,.2f}", "Upgrades, add-ons, extra compute credits")
    wf_table.add_row("Contraction MRR", f"-${wf['contraction_mrr']:,.2f}", "Plan downgrades")
    wf_table.add_row("Churned MRR", f"-${wf['churned_mrr']:,.2f}", "Cancelled or expired subscriptions")
    net_color = "green" if wf["net_new_mrr"] >= 0 else "red"
    wf_table.add_row(
        "[bold white]Net New MRR[/bold white]",
        f"[bold {net_color}]${wf['net_new_mrr']:,.2f}[/bold {net_color}]",
        "Net change in recurring revenue baseline",
    )
    console.print(wf_table)

    tb = metrics.get("tier_breakdown", {})
    if tb:
        tier_table = Table(
            title="🏷️ Subscription Tier Distribution",
            box=ROUNDED,
            show_header=True,
            header_style="bold yellow",
        )
        tier_table.add_column("Tier", style="bold")
        tier_table.add_column("Active Subscribers", justify="center")
        tier_table.add_column("MRR Contribution", justify="right")

        for tier_name, tinfo in tb.items():
            tier_table.add_row(
                tier_name.capitalize(),
                str(tinfo["count"]),
                f"${tinfo['mrr']:,.2f}",
            )
        console.print(tier_table)


def render_reconciliation_report(console: Console, report: dict[str, Any]) -> None:
    """Render reconciliation summary and detected discrepancies."""
    status_color = "green" if report["status"] == "reconciled" else "yellow"
    panel_title = f"⚖️ Payment Reconciliation Report — [{status_color}]{report['status'].upper()}[/{status_color}]"

    summary_table = Table(box=ROUNDED, show_header=False)
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value")

    summary_table.add_row("Reconciliation ID", report["id"])
    summary_table.add_row("Period", report["period"])
    summary_table.add_row("Total Expected", f"${report['total_expected']:,.2f} USD")
    summary_table.add_row("Total Collected", f"${report['total_collected']:,.2f} USD")
    summary_table.add_row(
        "Net Discrepancy",
        f"[{status_color}]${report['net_discrepancy']:,.2f} USD[/{status_color}]",
    )
    summary_table.add_row("Discrepancies Count", str(report["discrepancies_count"]))
    summary_table.add_row("Auto-Fix Applied", str(report["auto_fix_applied"]))

    console.print(Panel(summary_table, title=panel_title, border_style=status_color, box=ROUNDED))

    if report["discrepancies"]:
        disc_table = Table(
            title="⚠️ Detected Discrepancies",
            box=ROUNDED,
            header_style="bold red",
        )
        disc_table.add_column("Customer ID", style="bold")
        disc_table.add_column("Type")
        disc_table.add_column("Expected", justify="right")
        disc_table.add_column("Collected", justify="right")
        disc_table.add_column("Message", style="dim")

        for d in report["discrepancies"]:
            disc_table.add_row(
                d["customer_id"],
                d["type"],
                f"${d['expected']:,.2f}",
                f"${d['collected']:,.2f}",
                d["message"],
            )
        console.print(disc_table)


def render_forecast_report(console: Console, fc: dict[str, Any], scenario: str) -> None:
    """Render revenue forecast projections."""
    summary_panel = Panel(
        f"Scenario: [bold cyan]{fc['scenario'].upper()}[/bold cyan] | "
        f"Horizon: [bold]{fc['horizon_months']} months[/bold] | "
        f"Net MoM: [bold green]+{fc['net_monthly_growth_pct']}%[/bold green]\n"
        f"Starting MRR: [bold]${fc['starting_mrr']:,.2f}[/bold] ➡️ "
        f"Projected MRR: [bold green]${fc['projected_ending_mrr']:,.2f}[/bold green] | "
        f"Projected ARR: [bold cyan]${fc['projected_ending_arr']:,.2f}[/bold cyan]\n"
        f"Total Expected Inflow: [bold yellow]${fc['total_forecasted_revenue']:,.2f}[/bold yellow]",
        title=f"🔮 Revenue Forecast Projections ({scenario.capitalize()})",
        border_style="cyan",
        box=ROUNDED,
    )
    console.print(summary_panel)

    table = Table(box=ROUNDED, show_header=True, header_style="bold blue")
    table.add_column("Month", justify="center")
    table.add_column("Projected MRR", justify="right")
    table.add_column("Projected ARR", justify="right")
    table.add_column("Cumulative Revenue", justify="right", style="green")

    for p in fc["monthly_projections"]:
        table.add_row(
            f"Month +{p['month']}",
            f"${p['projected_mrr']:,.2f}",
            f"${p['projected_arr']:,.2f}",
            f"${p['cumulative_revenue']:,.2f}",
        )
    console.print(table)
