"""CLI commands for Constitutional Treasury (``mekong particle zenpay``).

Wires into ``particle_app`` in ``app_setup.py`` as a sub-app::

    mekong particle zenpay record <particle> <tx_type> <amount> <description>
    mekong particle zenpay balance <particle>
    mekong particle zenpay history <particle>
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from src.mekong.treasury.models import (
    Currency,
    Transaction,
    TransactionKind,
    TransactionStatus,
    TreasuryError,
)
from src.mekong.zenpay.treasury import (
    get_balance,
    get_history,
    record_transaction,
)

zenpay_app = typer.Typer(
    name="zenpay",
    help="Constitutional Treasury — record transactions and manage budgets",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _fail(msg: str, code: int = 1) -> None:
    console.print(f"[bold red]Error:[/] {msg}")
    raise typer.Exit(code=code)


_KIND_MAP = {
    "income": TransactionKind.INCOME,
    "expense": TransactionKind.WITHDRAWAL,
    "transfer": TransactionKind.WITHDRAWAL,
}


@zenpay_app.command(name="record")
def record_cmd(
    particle: str = typer.Argument(..., help="Particle ID (e.g. particle:alpha)"),
    tx_type: str = typer.Argument(..., help="Transaction type — income | expense | transfer"),
    amount: float = typer.Argument(..., help="Transaction amount"),
    description: str = typer.Argument(..., help="Human-readable description of the transaction"),
    currency: str = typer.Option("USD", "--currency", "-c", help="ISO 4217 currency code"),
    category: str = typer.Option("revenue", "--category", "-C", help="Business category"),
    counterparty: str | None = typer.Option(None, "--counterparty", "-p", help="Counterparty identifier"),
) -> None:
    """Record a treasury transaction with constitutional review."""
    kind = _KIND_MAP.get(tx_type.strip().lower())
    if kind is None:
        _fail(f"Unsupported tx_type={tx_type!r}. Allowed: income, expense, transfer")
    try:
        tx = Transaction(
            tx_id="",
            kind=kind,
            currency=Currency(currency.upper()),
            amount=amount,
            bucket=category,
            source=description,
            destination=counterparty or "",
            status=TransactionStatus.PENDING,
        )
        result = record_transaction(tx, requested_by=particle)
    except (ValueError, FileNotFoundError, RuntimeError, TreasuryError) as exc:
        _fail(str(exc))
    console.print(
        f"[green]Transaction recorded[/]\n"
        f" Transaction ID: [cyan]{result['transaction_id']}[/]\n"
        f" Behavior ID: [cyan]{result['behavior_id']}[/]\n"
        f" Review Status: [cyan]{result['review_status']}[/]"
    )


@zenpay_app.command(name="balance")
def balance_cmd(
    particle: str = typer.Argument(..., help="Particle ID (e.g. particle:alpha)"),
) -> None:
    """Show treasury balance for a particle."""
    try:
        bal = get_balance(particle)
    except (ValueError, FileNotFoundError, RuntimeError, TreasuryError) as exc:
        _fail(str(exc))
    console.print(
        f"[bold]Treasury Balance[/] — [cyan]{bal.particle_id}[/]\n"
        f" Total Income: [green]{bal.total_income:,.2f}[/]\n"
        f" Total Expense: [red]{bal.total_expense:,.2f}[/]\n"
        f" Net Balance: [bold]{bal.net_balance:,.2f}[/]\n"
        f" Transactions: {bal.transaction_count}"
    )
    if bal.buckets:
        console.print(" [dim]Buckets:[/]")
        for name, amt in bal.buckets.items():
            console.print(f"   {name}: [cyan]{amt:,.2f}[/]")


@zenpay_app.command(name="history")
def history_cmd(
    particle: str = typer.Argument(..., help="Particle ID (e.g. particle:alpha)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of recent transactions to show"),
) -> None:
    """Show recent treasury transactions, newest first."""
    try:
        transactions = get_history(particle, limit=limit)
    except (ValueError, FileNotFoundError, RuntimeError, TreasuryError) as exc:
        _fail(str(exc))
    if not transactions:
        console.print("[yellow]No treasury transactions found.[/]")
        return
    table = Table(title=f"Treasury History — {particle}")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Type", style="cyan")
    table.add_column("Amount", justify="right")
    table.add_column("Description")
    table.add_column("Category")
    table.add_column("Review", style="yellow")
    table.add_column("Timestamp", style="dim")
    for tx in transactions:
        amount_str = f"{tx.amount:,.2f} {tx.currency}"
        review_style = "green" if tx.constitutional_review == "passed" else "red"
        table.add_row(
            tx.id[:8],
            tx.tx_type,
            amount_str,
            tx.description,
            tx.category,
            f"[{review_style}]{tx.constitutional_review}[/]",
            tx.timestamp,
        )
    console.print(table)
