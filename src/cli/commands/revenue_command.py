# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command surface for Revenue Operations & Financial Intelligence Suite."""

from __future__ import annotations

import json

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

from src.cli.commands._revenue_renderers import (
    render_forecast_report,
    render_reconciliation_report,
    render_revenue_dashboard,
)
from src.cli.commands._revenue_subscriptions import (
    revenue_catalog,
    subscription_app,
    subscription_cancel,
    subscription_create,
    subscription_list,
)
from src.core.revenue_engine import get_revenue_engine

console = Console()
revenue_app = typer.Typer(
    name="revenue",
    help="💰 Revenue Operations & Financial Intelligence: MRR/ARR waterfall, reconciliation, and forecasting",
    no_args_is_help=False,
)
revenue_app.add_typer(subscription_app, name="subscription")
revenue_app.command("catalog")(revenue_catalog)


@revenue_app.callback(invoke_without_command=True)
def revenue_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON revenue operations overview"),
) -> None:
    """💰 Revenue Operations Overview: Executive financial health, MRR/ARR waterfall, and ledger metrics."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_revenue_engine()
    metrics = engine.get_metrics()
    status = engine.get_status()

    if json_output:
        print(json.dumps({**status, "metrics": metrics}, indent=2))
        return

    render_revenue_dashboard(console, metrics, status)


@revenue_app.command("metrics")
def revenue_metrics(
    period: str = typer.Option("month", "--period", "-p", help="Reporting period: month, quarter, year"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON metrics"),
) -> None:
    """📊 Compute MRR, ARR, ARPU, LTV, churn rate, and waterfall economics."""
    metrics = get_revenue_engine().get_metrics(period=period)
    if json_output:
        print(json.dumps(metrics, indent=2))
        return

    table = Table(title=f"📊 Financial Economics & Metrics ({period.capitalize()})", box=ROUNDED, header_style="bold green")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Context", style="dim")
    for k, v, c in [
        ("MRR", f"${metrics['mrr']:,.2f}", "Monthly Recurring Revenue baseline"),
        ("ARR", f"${metrics['arr']:,.2f}", "Annualized Run Rate (MRR × 12)"),
        ("Total Succeeded Revenue", f"${metrics['total_revenue']:,.2f}", "Cumulative collected cash"),
        ("Paying Customers", str(metrics["paying_customers"]), "Unique accounts with active plan"),
        ("ARPU", f"${metrics['arpu']:,.2f}", "Average Revenue Per User"),
        ("Customer LTV", f"${metrics['ltv']:,.2f}", "Estimated Lifetime Value"),
        ("Churn Rate", f"{metrics['churn_rate_pct']}%", "Subscription cancellations"),
        ("NRR", f"{metrics['nrr_pct']}%", "Net Revenue Retention"),
    ]:
        table.add_row(k, v, c)
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
    res = get_revenue_engine().record_transaction(
        customer_id=customer_id, amount=amount, customer_name=customer_name, currency=currency,
        tier=tier, type=txn_type, gateway=gateway, status=status, notes=notes, auto_subscription=auto_subscription,
    )
    if json_output:
        print(json.dumps(res, indent=2))
        return

    table = Table(title="✅ Transaction Successfully Recorded", box=ROUNDED, header_style="bold green")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    for k, v in [
        ("Transaction ID", f"[cyan]{res['id']}[/cyan]"),
        ("Customer", f"{res['customer_name']} ({res['customer_id']})"),
        ("Amount", f"{res['amount']:,.2f} {res['currency']} (~${res['amount_usd']:,.2f} USD)"),
        ("Tier / Type", f"{res['tier']} / {res['type']}"),
        ("Gateway", res["gateway"]),
        ("Status", f"[bold green]{res['status']}[/bold green]"),
    ]:
        table.add_row(k, v)
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
    report = get_revenue_engine().reconcile_payments(auto_fix=auto_fix)
    print(json.dumps(report, indent=2)) if json_output else render_reconciliation_report(console, report)


@revenue_app.command("forecast")
def revenue_forecast(
    months: int = typer.Option(6, "--months", "-m", help="Projection horizon in months (e.g. 3, 6, 12)"),
    scenario: str = typer.Option("base", "--scenario", "-s", help="Growth scenario: conservative, base, aggressive"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON forecast"),
) -> None:
    """🔮 Project future MRR, ARR, and cumulative revenue under growth scenarios."""
    fc = get_revenue_engine().forecast_revenue(months=months, scenario=scenario)
    print(json.dumps(fc, indent=2)) if json_output else render_forecast_report(console, fc, scenario)


def register_revenue_command(app: typer.Typer) -> None:
    """Register the 'revenue' command group onto the main Typer application."""
    app.add_typer(revenue_app, name="revenue")


__all__ = [
    "revenue_app", "subscription_app", "revenue_main", "revenue_metrics", "revenue_record",
    "revenue_reconcile", "revenue_forecast", "revenue_catalog", "subscription_create",
    "subscription_list", "subscription_cancel", "register_revenue_command",
]
