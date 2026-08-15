"""Mekong CLI 7 — OPC Business Loop commands: signal/revenue/metrics/loop."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.opc_loop import OpcLoop

console = Console()


def signal_add_cmd(
    product: str = typer.Argument(..., help="Product name"),
    kind: str = typer.Argument(..., help="lead|inbound|support|idea|failure|competitor"),
    note: str = typer.Option("", "--note", help="Note"),
) -> None:
    """Add a market signal (OBSERVE phase input)."""
    loop = OpcLoop()
    loop.signals.add(product, kind, note)
    console.print(f"[green]✓ signal added[/] {product} ({kind})" + (f" — {note}" if note else ""))


def signal_list_cmd(
    product: Optional[str] = typer.Argument(None, help="Filter by product"),
) -> None:
    """List signals in the inbox."""
    loop = OpcLoop()
    sigs = loop.signals.list(product)
    if not sigs:
        console.print("[yellow]Inbox trống — thêm signal: mk signal add <product> <kind>[/]")
        return
    table = Table(title=f"Signal Inbox ({len(sigs)})")
    table.add_column("Product")
    table.add_column("Kind")
    table.add_column("Time")
    table.add_column("Note")
    for prod, s in sigs:
        ts = __import__("time").strftime("%m-%d %H:%M", __import__("time").localtime(s["ts"]))
        table.add_row(prod, s["kind"], ts, s.get("note", "")[:40])
    console.print(table)


def revenue_add_cmd(
    product: str = typer.Argument(..., help="Product name"),
    amount: float = typer.Argument(..., help="Amount"),
    confirmed_by: str = typer.Option(..., "--by", prompt=True, help="Human who confirmed"),
    currency: str = typer.Option("USD", "--currency"),
    kind: str = typer.Option("sale", "--kind", help="sale|subscription|milestone"),
) -> None:
    """Record revenue (REVENUE phase — bắt buộc human confirm)."""
    loop = OpcLoop()
    loop.revenue.record(product, amount, currency=currency, kind=kind, confirmed_by=confirmed_by)
    console.print(f"[green]✓ revenue recorded[/] {product} +{amount} {currency} (by {confirmed_by})")


def metrics_cmd() -> None:
    """Show per-product metrics + kill recommendations."""
    loop = OpcLoop()
    table = Table(title="Product Metrics")
    table.add_column("Product")
    table.add_column("Cycles")
    table.add_column("Revenue")
    table.add_column("Rev/Hour")
    table.add_column("Zero-streak")
    table.add_column("Status")
    for prod in loop.state.active_products:
        m = loop.metrics.get(prod)
        rev = loop.revenue.total_for(prod)
        hours = m.get("build_cost_hours", 0) or 1
        status = "ACTIVE"
        if m.get("zero_revenue_streak", 0) >= loop.kill_cycles:
            status = "🔴 KILL"
        table.add_row(prod, str(m.get("cycles", 0)), f"{rev}$",
                      str(round(rev / hours, 2)), str(m.get("zero_revenue_streak", 0)), status)
    for prod in loop.state.archived_products:
        table.add_row(prod, "-", "-", "-", "-", "🗄️ archived")
    if not loop.state.active_products and not loop.state.archived_products:
        console.print("[yellow]Chưa có product nào — thêm product: mk loop --add-product <name>[/]")
        return
    console.print(table)


def loop_cmd(
    dry_run: bool = typer.Option(True, "--no-dry-run", help="Chạy build thật (mặc định dry-run)"),
    add_product: Optional[str] = typer.Option(None, "--add-product", help="Thêm product rồi loop"),
    once: bool = typer.Option(False, "--once", help="Chạy 1 cycle rồi thoát"),
    kill_cycles: Optional[int] = typer.Option(None, "--kill-cycles",
                                              help="Set kill threshold ($0 revenue sau N cycles → archive)"),
) -> None:
    """Run one OPC business loop cycle (OBSERVE→DECIDE→BUILD→SELL→REVENUE→LEARN→OPTIMIZE)."""
    loop = OpcLoop()
    if kill_cycles is not None:
        if kill_cycles < 1:
            console.print("[red]kill_cycles phải >= 1[/]")
            return
        loop.state.kill_cycles = kill_cycles
        loop.state.save()
        console.print(f"[green]✓ kill_cycles set = {kill_cycles}[/] "
                      f"($0 revenue sau {kill_cycles} cycles → archive)")
        if not once:
            return
        if add_product not in loop.state.active_products:
            loop.state.active_products.append(add_product)
            loop.metrics.update(add_product, cycles=0, revenue_total=0.0)
            loop.state.save()
            console.print(f"[green]✓ product added[/] {add_product}")
    if not loop.state.active_products:
        console.print("[yellow]Không có product active — dùng --add-product <name> hoặc sửa ~/.mekong/opc/loop-state.json[/]")
        return
    report = loop.run_cycle(dry_run=not dry_run)
    console.print(f"[bold cyan]=== CYCLE {report['cycle']} ===[/]")
    console.print(f"[bold]OBSERVE:[/] {report['observe']['total']} signals")
    d = report["decide"]
    console.print(f"[bold]DECIDE:[/] keep={d['keep']} kill={d['kill']}")
    for prod, b in report.get("build", {}).items():
        console.print(f"[bold]BUILD {prod}:[/] {b['status']}")
    for prod, s in report.get("sell", {}).items():
        console.print(f"[bold]SELL {prod}:[/] {s['status']} ({s['note']})")
    for prod, l in report.get("learn", {}).items():
        console.print(f"[bold]LEARN {prod}:[/] rev={l['revenue']}$ rev/hr={l['revenue_per_hour']}")
    for prod, o in report.get("optimize", {}).items():
        console.print(f"[bold]OPTIMIZE {prod}:[/] {o.get('hint', o.get('reason', ''))}")
    if not dry_run:
        console.print("[yellow]NOTE: build thật đang tắt — bật bằng --no-dry-run[/]")
