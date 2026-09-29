# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/revenue_command.py — CLI command surface for Revenue Operations & Financial Intelligence Suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.revenue_engine import get_revenue_engine

console = Console()
revenue_app = typer.Typer(
    name="revenue",
    help="💰 Revenue Operations & Financial Intelligence: MRR/ARR waterfall, reconciliation, and forecasting",
    no_args_is_help=False,
)

subscription_app = typer.Typer(
    name="subscription",
    help="📋 Customer subscription management and lifecycle tracking",
    no_args_is_help=False,
)
revenue_app.add_typer(subscription_app, name="subscription")


@revenue_app.callback(invoke_without_command=True)
def revenue_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON revenue operations overview",
    ),
) -> None:
    """💰 Revenue Operations Overview: Executive financial health, MRR/ARR waterfall, and ledger metrics."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_revenue_engine()
    metrics = engine.get_metrics()
    status = engine.get_status()

    if json_output:
        summary = {**status, "metrics": metrics}
        print(json.dumps(summary, indent=2))
        return

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

    # MRR Waterfall table
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
    wf_table.add_row(
        "[bold white]Net New MRR[/bold white]",
        f"[bold {'green' if wf['net_new_mrr'] >= 0 else 'red'}]${wf['net_new_mrr']:,.2f}[/bold {'green' if wf['net_new_mrr'] >= 0 else 'red'}]",
        "Net change in recurring revenue baseline",
    )
    console.print(wf_table)

    # Tier Breakdown Table
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


@revenue_app.command("metrics")
def revenue_metrics(
    period: str = typer.Option("month", "--period", "-p", help="Reporting period: month, quarter, year"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON metrics"),
) -> None:
    """📊 Compute MRR, ARR, ARPU, LTV, churn rate, and waterfall economics."""
    engine = get_revenue_engine()
    metrics = engine.get_metrics(period=period)

    if json_output:
        print(json.dumps(metrics, indent=2))
        return

    table = Table(
        title=f"📊 Financial Economics & Metrics ({period.capitalize()})",
        box=ROUNDED,
        header_style="bold green",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Context", style="dim")

    table.add_row("MRR", f"${metrics['mrr']:,.2f}", "Monthly Recurring Revenue baseline")
    table.add_row("ARR", f"${metrics['arr']:,.2f}", "Annualized Run Rate (MRR × 12)")
    table.add_row("Total Succeeded Revenue", f"${metrics['total_revenue']:,.2f}", "Cumulative collected cash")
    table.add_row("Paying Customers", str(metrics["paying_customers"]), "Unique accounts with active plan")
    table.add_row("ARPU", f"${metrics['arpu']:,.2f}", "Average Revenue Per User")
    table.add_row("Customer LTV", f"${metrics['ltv']:,.2f}", "Estimated Lifetime Value")
    table.add_row("Churn Rate", f"{metrics['churn_rate_pct']}%", "Subscription cancellations")
    table.add_row("NRR", f"{metrics['nrr_pct']}%", "Net Revenue Retention")

    console.print(table)


@revenue_app.command("record")
def revenue_record(
    customer_id: str = typer.Argument(..., help="Customer identifier or account ID"),
    amount: float = typer.Option(..., "--amount", "-a", help="Transaction amount in currency"),
    customer_name: str = typer.Option("", "--name", "-n", help="Customer or company display name"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency: USD or VND"),
    tier: str = typer.Option("starter", "--tier", "-t", help="Subscription tier or plan name"),
    txn_type: str = typer.Option("subscription", "--type", help="Transaction type: subscription, one_time, addon, refund"),
    gateway: str = typer.Option("stripe", "--gateway", "-g", help="Payment gateway: stripe, polar, bank_transfer, manual"),
    status: str = typer.Option("succeeded", "--status", "-s", help="Transaction status: succeeded, pending, failed, refunded"),
    notes: str = typer.Option("", "--notes", help="Optional internal payment notes"),
    auto_subscription: bool = typer.Option(True, "--auto-sub/--no-auto-sub", help="Automatically create/renew customer subscription"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON confirmation"),
) -> None:
    """💳 Record a transaction into the revenue ledger."""
    engine = get_revenue_engine()
    res = engine.record_transaction(
        customer_id=customer_id,
        amount=amount,
        customer_name=customer_name,
        currency=currency,
        tier=tier,
        type=txn_type,
        gateway=gateway,
        status=status,
        notes=notes,
        auto_subscription=auto_subscription,
    )

    if json_output:
        print(json.dumps(res, indent=2))
        return

    table = Table(
        title="✅ Transaction Successfully Recorded",
        box=ROUNDED,
        header_style="bold green",
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Transaction ID", f"[cyan]{res['id']}[/cyan]")
    table.add_row("Customer", f"{res['customer_name']} ({res['customer_id']})")
    table.add_row("Amount", f"{res['amount']:,.2f} {res['currency']} (~${res['amount_usd']:,.2f} USD)")
    table.add_row("Tier / Type", f"{res['tier']} / {res['type']}")
    table.add_row("Gateway", res["gateway"])
    table.add_row("Status", f"[bold green]{res['status']}[/bold green]")
    if res.get("subscription_id"):
        table.add_row("Subscription", f"[yellow]{res['subscription_id']}[/yellow]")
    if res.get("notes"):
        table.add_row("Notes", res["notes"])

    console.print(table)


@revenue_app.command("reconcile")
def revenue_reconcile(
    auto_fix: bool = typer.Option(False, "--auto-fix", "-f", help="Automatically flag unpaid subscriptions as past_due"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON reconciliation report"),
) -> None:
    """⚖️ Reconcile expected subscription dues against collected ledger transactions."""
    engine = get_revenue_engine()
    report = engine.reconcile_payments(auto_fix=auto_fix)

    if json_output:
        print(json.dumps(report, indent=2))
        return

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


@revenue_app.command("forecast")
def revenue_forecast(
    months: int = typer.Option(6, "--months", "-m", help="Projection horizon in months (e.g. 3, 6, 12)"),
    scenario: str = typer.Option("base", "--scenario", "-s", help="Growth scenario: conservative, base, aggressive"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON forecast"),
) -> None:
    """🔮 Project future MRR, ARR, and cumulative revenue under growth scenarios."""
    engine = get_revenue_engine()
    fc = engine.forecast_revenue(months=months, scenario=scenario)

    if json_output:
        print(json.dumps(fc, indent=2))
        return

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


@revenue_app.command("catalog")
def revenue_catalog(
    currency: str = typer.Option("USD", "--currency", "-c", help="Currency display: USD or VND"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON catalog"),
) -> None:
    """🏷️ Display official subscription tier pricing and compute credit allocations."""
    engine = get_revenue_engine()
    catalog = engine.get_tier_catalog(currency=currency)

    if json_output:
        print(json.dumps(catalog, indent=2))
        return

    table = Table(
        title=f"🏷️ Mekong Official Pricing & Tiers ({currency.upper()})",
        box=ROUNDED,
        header_style="bold yellow",
    )
    table.add_column("Tier", style="bold")
    table.add_column("Name")
    table.add_column("Price / Month", justify="right")
    table.add_column("MCU Credits", justify="center")
    table.add_column("Features & Target", style="dim")

    for tier_key, item in catalog.items():
        table.add_row(
            tier_key,
            item["name"],
            f"[bold green]{item['price_formatted']}[/bold green]",
            str(item["credits"]),
            item["description"],
        )

    console.print(table)


# --- Subscriptions Subcommands ---


@subscription_app.command("create")
def subscription_create(
    customer_id: str = typer.Argument(..., help="Customer identifier"),
    tier: str = typer.Option("starter", "--tier", "-t", help="Plan tier (starter, growth, scale, pro, enterprise)"),
    amount: Optional[float] = typer.Option(None, "--amount", "-a", help="Custom USD amount (defaults to catalog price)"),
    customer_name: str = typer.Option("", "--name", "-n", help="Customer display name"),
    billing_cycle: str = typer.Option("monthly", "--cycle", help="Billing frequency: monthly or annual"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON result"),
) -> None:
    """➕ Create or provision an active customer subscription."""
    engine = get_revenue_engine()
    res = engine.create_or_renew_subscription(
        customer_id=customer_id,
        tier=tier,
        amount_usd=amount,
        customer_name=customer_name,
        billing_cycle=billing_cycle,
    )

    if json_output:
        print(json.dumps(res, indent=2))
        return

    console.print(
        f"[bold green]✅ Subscription {res['action'].capitalize()}:[/bold green] "
        f"[cyan]{res['id']}[/cyan] for [bold]{res['customer_name']}[/bold] "
        f"({res['tier'].capitalize()} @ ${res['amount_usd']:,.2f}/mo)"
    )


@subscription_app.command("list")
def subscription_list(
    status: str = typer.Option("all", "--status", "-s", help="Filter by status: active, cancelled, past_due, all"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON subscriptions list"),
) -> None:
    """📋 List customer subscriptions with tier, billing, and status tracking."""
    engine = get_revenue_engine()
    subs = engine.list_subscriptions(status=status)

    if json_output:
        print(json.dumps(subs, indent=2))
        return

    if not subs:
        console.print(f"[yellow]No subscriptions found matching status '{status}'.[/yellow]")
        return

    table = Table(
        title=f"📋 Subscriptions Ledger ({status.capitalize()})",
        box=ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("Sub ID", style="bold cyan")
    table.add_column("Customer")
    table.add_column("Tier")
    table.add_column("MRR (USD)", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Started At", style="dim")

    for s in subs:
        stat_color = "green" if s["status"] == "active" else "red" if s["status"] == "cancelled" else "yellow"
        table.add_row(
            s["id"],
            f"{s['customer_name']} ({s['customer_id']})",
            s["tier"].capitalize(),
            f"${s['amount_usd']:,.2f}",
            f"[{stat_color}]{s['status']}[/{stat_color}]",
            s["started_at"][:10],
        )

    console.print(table)


@subscription_app.command("cancel")
def subscription_cancel(
    subscription_id: str = typer.Argument(..., help="Subscription ID or Customer ID to cancel"),
    reason: str = typer.Option("Customer request", "--reason", "-r", help="Cancellation rationale"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON result"),
) -> None:
    """🛑 Cancel an active customer subscription."""
    engine = get_revenue_engine()
    res = engine.cancel_subscription(subscription_id=subscription_id, reason=reason)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if res.get("success"):
        console.print(
            f"[bold red]🛑 Subscription Cancelled:[/bold red] [cyan]{res['id']}[/cyan] "
            f"for customer [bold]{res['customer_id']}[/bold]. Reason: {reason}"
        )
    else:
        console.print(f"[bold red]Error:[/bold red] {res.get('error')}")


def register_revenue_command(app: typer.Typer) -> None:
    """Register the 'revenue' command group onto the main Typer application."""
    app.add_typer(revenue_app, name="revenue")
