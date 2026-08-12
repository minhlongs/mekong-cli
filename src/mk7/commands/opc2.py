"""Mekong CLI 7 — OPC Platform commands: finance/analytics/sales/support/marketing/opc."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.analytics import Analytics
from ..core.finance import Finance
from ..core.marketing import Marketing
from ..core.profile import (DEFAULT_PROFILE, active_profile, init_profile,
                            list_profiles, set_active_profile)
from ..core.sales import SalesPipeline
from ..core.support import SupportDesk

console = Console()


# ── Finance ──────────────────────────────────────────────────

def cost_add_cmd(
    product: str = typer.Argument(...),
    hours: float = typer.Argument(..., help="Build hours"),
    by: str = typer.Option(..., "--by", prompt=True, help="Human who confirmed"),
    rate: float = typer.Option(50.0, "--rate", help="USD/hour"),
    tooling: float = typer.Option(0.0, "--tooling", help="Tooling USD"),
) -> None:
    """Record build cost (human confirmed)."""
    f = Finance()
    entry = f.costs.record(product, hours, rate=rate, tooling=tooling, by=by)
    console.print(f"[green]✓ cost recorded[/] {product}: {hours}h × {rate}$ = {entry.total_usd}$ (by {by})")


def finance_cmd() -> None:
    """Show finance summary: revenue/cost/profit/MRR per product."""
    f = Finance()
    summary = f.summary()
    table = Table(title=f"Finance — MRR total: {summary['mrr_total']}$")
    table.add_column("Product")
    table.add_column("Revenue")
    table.add_column("Cost")
    table.add_column("Profit")
    table.add_column("Hours")
    table.add_column("MRR")
    for p, d in summary["products"].items():
        table.add_row(p, f"{d['revenue']}$", f"{d['cost']}$", f"{d['profit']}$",
                      str(d["hours"]), f"{d['mrr']}$")
    if not summary["products"]:
        console.print("[yellow]Chưa có data — mk revenue-add + mk cost-add[/]")
        return
    console.print(table)


# ── Analytics ────────────────────────────────────────────────

def analytics_cmd() -> None:
    """Show 4 KPI board."""
    a = Analytics()
    board = a.board()
    kpi = board["kpi"]
    table = Table(title="OPC Platform — 4 KPI")
    table.add_column("KPI")
    table.add_column("Value")
    table.add_row("MRR (30d subscriptions)", f"{kpi['mrr']}$")
    table.add_row("Active products", str(kpi["active_products"]))
    table.add_row("Conversion (closes/leads)", str(kpi["conversion"]) if kpi["conversion"] is not None else "n/a — cần leads")
    table.add_row("Cost per build hour", str(kpi["cost_per_build_hour"]) if kpi["cost_per_build_hour"] is not None else "n/a — cần cost")
    console.print(table)
    if board["products"]:
        ptable = Table(title="Per-product")
        ptable.add_column("Product")
        ptable.add_column("Revenue")
        ptable.add_column("Cost")
        ptable.add_column("Profit")
        ptable.add_column("Cycles")
        ptable.add_column("Kill-risk")
        for p in board["products"]:
            ptable.add_row(p["product"], f"{p['revenue']}$", f"{p['cost']}$",
                           f"{p['profit']}$", str(p["cycles"]), str(p["kill_risk"]))
        console.print(ptable)


# ── Sales ────────────────────────────────────────────────────

def sales_cmd(product: Optional[str] = typer.Argument(None)) -> None:
    """Sales pipeline: sync leads từ signals, xem stages."""
    s = SalesPipeline()
    created = s.create_from_signals()
    if created:
        console.print(f"[green]✓ {created} leads created từ signals[/]")
    leads = s.list(product)
    if not leads:
        console.print("[yellow]Không có lead — thêm signal: mk signal-add <product> lead <note>[/]")
        return
    table = Table(title="Sales pipeline")
    table.add_column("ID")
    table.add_column("Product")
    table.add_column("Stage")
    table.add_column("Note")
    for l in leads:
        table.add_row(l["id"], l["product"], l["stage"], l.get("note", "")[:40])
    console.print(table)


def sales_advance_cmd(
    lead_id: str = typer.Argument(...),
    stage: str = typer.Argument(..., help="new|contacted|proposal|closed"),
    amount: float = typer.Option(0.0, "--amount", help="Amount khi close"),
    by: str = typer.Option("", "--by", help="Human confirm khi close"),
) -> None:
    """Advance lead stage; close → ghi revenue."""
    s = SalesPipeline()
    if stage == "closed":
        if amount <= 0:
            console.print("[red]--amount bắt buộc khi close[/]")
            raise typer.Exit(1)
        lead = s.close(lead_id, amount, by)
        console.print(f"[green]✓ closed {lead['product']} +{amount}$ (by {by})[/]")
    else:
        lead = s.advance(lead_id, stage)
        console.print(f"[green]✓ lead {lead_id} → {stage}[/]")


def sales_proposal_cmd(lead_id: str = typer.Argument(...)) -> None:
    """Draft proposal cho lead (human review trước khi gửi)."""
    s = SalesPipeline()
    console.print(s.draft_proposal(lead_id))


# ── Support ──────────────────────────────────────────────────

def support_cmd(status: Optional[str] = typer.Option(None, "--status")) -> None:
    """Support desk: sync tickets từ signals."""
    d = SupportDesk()
    created = d.create_from_signals()
    if created:
        console.print(f"[green]✓ {created} tickets created từ signals[/]")
    tickets = d.list(status)
    if not tickets:
        console.print("[yellow]Không có ticket — thêm signal: mk signal-add <product> support <note>[/]")
        return
    table = Table(title="Support tickets")
    table.add_column("ID")
    table.add_column("Product")
    table.add_column("Status")
    table.add_column("Note")
    for t in tickets:
        table.add_row(t["id"], t["product"], t["status"], t.get("note", "")[:40])
    console.print(table)


def support_response_cmd(ticket_id: str = typer.Argument(...)) -> None:
    """Draft response cho ticket (human review trước khi gửi)."""
    d = SupportDesk()
    console.print(d.draft_response(ticket_id))


def support_resolve_cmd(
    ticket_id: str = typer.Argument(...),
    by: str = typer.Option(..., "--by", prompt=True),
) -> None:
    """Resolve ticket (human confirm)."""
    d = SupportDesk()
    t = d.resolve(ticket_id, by)
    console.print(f"[green]✓ ticket {ticket_id} resolved (by {by})[/]")


# ── Marketing ────────────────────────────────────────────────

def marketing_cmd(product: str = typer.Argument(...), angle: str = typer.Option("", "--angle")) -> None:
    """Draft marketing campaign (human review trước khi gửi)."""
    m = Marketing()
    console.print(m.draft(product, angle))


# ── LLM spend (A2) ───────────────────────────────────────────

def spend_cmd(
    hours: int = typer.Option(24, "--hours", help="Window (h) — 24 or 168"),
) -> None:
    """Show LLM spend per model: burn rate 24h/7d."""
    from ..core.spend import burn_rate, spend_summary

    s = spend_summary(hours)
    table = Table(title=f"LLM Spend — last {hours}h (real usage)")
    table.add_column("Model")
    table.add_column("Calls")
    table.add_column("In tokens")
    table.add_column("Out tokens")
    table.add_column("Cost ($)")
    for model, row in sorted(s["models"].items(), key=lambda kv: -kv[1]["cost"]):
        table.add_row(model, str(row["calls"]), str(row["input_tokens"]),
                      str(row["output_tokens"]), f"{row['cost']:.4f}")
    t = s["totals"]
    table.add_row("[bold]TOTAL[/]", str(t["calls"]), str(t["input_tokens"]),
                  str(t["output_tokens"]), f"[bold]{t['cost']:.4f}[/]")
    console.print(table)
    console.print(f"burn_rate(24h) = [bold]{burn_rate(24)}$[/] | "
                  f"burn_rate(7d) = [bold]{burn_rate(24 * 7)}$[/]")


# ── Provider breaker (A1) ────────────────────────────────────

def breaker_cmd(
    reset: bool = typer.Option(False, "--reset", help="Clear all lockouts + learned limits"),
) -> None:
    """Show breaker lockout state + learned rate limits."""
    from ..core.resilience import breaker

    if reset:
        breaker.clear()
        console.print("[green]✓ breaker cleared[/] (lockouts + learned limits)")
        return
    locked = breaker.locked_models()
    if locked:
        table = Table(title="Breaker lockouts")
        table.add_column("Provider")
        table.add_column("Model")
        table.add_column("Remaining (s)")
        table.add_column("Reason")
        for d in locked:
            table.add_row(d["provider"], d["model"], f"{d['remaining']:.0f}", d["reason"] or "—")
        console.print(table)
    else:
        console.print("[green]✓ no active lockouts[/]")
    limits = breaker.rate_limits()
    if limits:
        ltable = Table(title="Learned rate limits (B7)")
        ltable.add_column("Model")
        ltable.add_column("Remaining")
        ltable.add_column("Reset in (s)")
        for model, e in sorted(limits.items()):
            ltable.add_row(model, str(e.get("remaining", "?")), str(e.get("reset_in", "?")))
        console.print(ltable)
    else:
        console.print("[yellow]learned rate limits: chưa có — sẽ học từ 429/headers[/]")


# ── OPC profile ──────────────────────────────────────────────

def opc_init_cmd(name: str = typer.Argument(...)) -> None:
    """Tạo profile OPC mới (productize — mỗi công ty 1 profile)."""
    p = init_profile(name)
    console.print(f"[green]✓ profile '{name}' created[/] state: {p}")


def opc_use_cmd(name: str = typer.Argument(...)) -> None:
    """Chuyển sang profile khác."""
    if name not in list_profiles() and name != DEFAULT_PROFILE:
        console.print(f"[red]Profile '{name}' chưa tồn tại — mk opc init {name}[/]")
        raise typer.Exit(1)
    set_active_profile(name)
    console.print(f"[green]✓ switched to profile '{name}'[/]")


def opc_list_cmd() -> None:
    """List profiles + profile đang dùng."""
    current = active_profile()
    console.print(f"Active: [bold]{current}[/]")
    for p in list_profiles():
        marker = "→" if p == current else " "
        console.print(f" {marker} {p}")
    if current == DEFAULT_PROFILE:
        console.print(f" {current} (default — state cũ ~/.mekong/opc)")
