# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Subscription lifecycle and catalog subcommands for Revenue Operations CLI."""

from __future__ import annotations

import json

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

from src.core.revenue_engine import get_revenue_engine

console = Console()
subscription_app = typer.Typer(
    name="subscription",
    help="🔁 Manage SaaS subscriptions: create, list, cancel, and inspect recurring accounts",
    no_args_is_help=True,
)


@subscription_app.command("create")
def subscription_create(
    customer_id: str = typer.Argument(..., help="Customer identifier"),
    tier: str = typer.Option("starter", "--tier", "-t", help="Tier: starter, pro, enterprise, agency"),
    customer_name: str = typer.Option("", "--name", "-n", help="Customer display name"),
    billing_cycle: str = typer.Option("monthly", "--cycle", "-c", help="Billing cycle: monthly or annual"),
    mrr_usd: float = typer.Option(-1.0, "--mrr", help="Custom MRR override in USD (leave default for tier price)"),
    status: str = typer.Option("active", "--status", "-s", help="Initial status: active, trialing, past_due"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """➕ Create or update a customer recurring subscription."""
    engine = get_revenue_engine()
    override = mrr_usd if mrr_usd >= 0 else None
    sub = engine.create_subscription(
        customer_id=customer_id,
        tier=tier,
        customer_name=customer_name,
        billing_cycle=billing_cycle,
        mrr_usd=override,
        status=status,
    )

    if json_output:
        print(json.dumps(sub, indent=2))
        return

    console.print(
        f"[bold green]✓ Subscription Created/Updated:[/bold green] [cyan]{sub['id']}[/cyan] "
        f"| Customer: [bold]{sub['customer_name']}[/bold] ({sub['customer_id']}) "
        f"| Tier: [yellow]{sub['tier']}[/yellow] "
        f"| MRR: [bold green]${sub['mrr_usd']:,.2f}/mo[/bold green]"
    )


@subscription_app.command("list")
def subscription_list(
    status: str = typer.Option("", "--status", "-s", help="Filter by status: active, canceled, past_due"),
    tier: str = typer.Option("", "--tier", "-t", help="Filter by tier"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """📋 List recurring subscriptions and MRR contributions."""
    engine = get_revenue_engine()
    subs = engine.list_subscriptions(
        status=status if status else None,
        tier=tier if tier else None,
    )

    if json_output:
        print(json.dumps(subs, indent=2))
        return

    if not subs:
        console.print("[yellow]No subscriptions found matching criteria.[/yellow]")
        return

    table = Table(
        title=f"🔁 Customer Subscriptions ({len(subs)} records)",
        box=ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim")
    table.add_column("Customer", style="bold")
    table.add_column("Tier", justify="center")
    table.add_column("Cycle", justify="center")
    table.add_column("MRR ($)", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Next Renewal", style="dim")

    for s in subs:
        st = s["status"]
        st_fmt = f"[green]{st}[/green]" if st in ("active", "trialing") else f"[red]{st}[/red]"
        table.add_row(
            s["id"],
            f"{s['customer_name']} ({s['customer_id']})",
            s["tier"],
            s["billing_cycle"],
            f"${s['mrr_usd']:,.2f}",
            st_fmt,
            s.get("current_period_end", "")[:10],
        )

    console.print(table)


@subscription_app.command("cancel")
def subscription_cancel(
    customer_id: str = typer.Argument(..., help="Customer ID or Subscription ID to cancel"),
    reason: str = typer.Option("Customer requested cancellation", "--reason", "-r", help="Churn reason for analytics"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON"),
) -> None:
    """🛑 Cancel an active subscription and record churn telemetry."""
    engine = get_revenue_engine()
    res = engine.cancel_subscription(customer_id=customer_id, reason=reason)

    if json_output:
        print(json.dumps(res, indent=2))
        return

    if res.get("canceled"):
        console.print(
            f"[bold yellow]⚠ Subscription Canceled:[/bold yellow] [cyan]{res['subscription_id']}[/cyan] "
            f"(Churned MRR: [red]-${res['churned_mrr_usd']:,.2f}[/red])"
        )
    else:
        console.print(f"[red]✗ Cancellation failed:[/red] {res.get('error', 'Unknown error')}")


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
