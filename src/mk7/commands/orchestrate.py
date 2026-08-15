"""Mekong CLI 7 — `orchestrate` command: 5-phase pipeline for solo CEO.

PLAN (kongming/strategist) -> PLAN GATE (suntzu, repeat-until 3 rounds)
-> EXECUTE (dispatch) -> RESULT GATE (suntzu) -> SHIP (commit/PR/deploy/smoke).
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.orchestrate import MAX_GATE_ROUNDS, run_pipeline
from ..core.sop import find, load_all

console = Console()


def orchestrate_cmd(
    task: str = typer.Argument(..., help="Task (or SOP name) in natural language"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan/gates only, skip ship"),
    agent: str = typer.Option("eng", "--agent", help="Execute agent (eng/pm/ops/ceo)"),
    model: str = typer.Option("fable", "--model", help="Gate model role (strategist/fable)"),
) -> None:
    """Orchestrate: Khổng Minh plan -> Tôn Tử gate -> execute -> gate -> ship."""
    console.print(Panel(f"⚔️  ORCHESTRATE — {task}", border_style="yellow"))

    from ..core.llm import LLMClient

    client = LLMClient()
    result = run_pipeline(task, client=client, dry_run=dry_run, execute_agent=agent)

    if not result.ok:
        console.print(f"[red]✗ FAILED at {result.phase}: {result.error[:500]}[/]")
        sys.exit(1)

    console.print(Panel(
        "🧠 KHỔNG MINH — PLAN\n"
        f"   {result.plan[:400]}...\n\n"
        "⚔️ TÔN TỬ — VERDICT (plan)\n"
        f"   {result.plan_verdict[:300]}...\n\n"
        "⚙️ EXECUTE\n"
        f"   {result.execution[-600:]}\n\n"
        "⚔️ TÔN TỬ — VERDICT (result)\n"
        f"   {result.result_verdict[:300]}...\n\n"
        "🚀 SHIP\n"
        f"   {result.ship_report[:800]}...",
        title="✅ GO-LIVE",
        border_style="green",
    ))
    sys.exit(0)


def sop_cmd(
    sop_name: str = typer.Argument(..., help="SOP name or keyword (e.g. incident-response)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Skip ship"),
    agent: str = typer.Option("ops", "--agent", help="Execute agent for this SOP"),
) -> None:
    """Run a SOP through the orchestrate pipeline (24/7 ops)."""
    sop = find(sop_name)
    if not sop is None:
        pass
    if sop is None:
        console.print("[yellow]Available SOPs:[/]")
        for d in load_all():
            console.print(f"  [bold]{d.layer}/{d.name}[/] — {d.intent[:60]}")
        sys.exit(1)

    console.print(Panel(f"📋 SOP — {sop.layer}/{sop.name}\n{sop.intent}", border_style="cyan"))
    from ..core.orchestrate import run_sop_pipeline
    from ..core.llm import LLMClient

    result = run_sop_pipeline(sop, client=LLMClient(), dry_run=dry_run, execute_agent=agent)
    if not result.ok:
        console.print(f"[red]✗ SOP failed at {result.phase}: {result.error[:500]}[/]")
        sys.exit(1)
    console.print(Panel(
        f"📋 {sop.layer}/{sop.name}\n⚔️ gates PASS/CONDITIONAL PASS\n🚀 {result.ship_report[:600]}",
        title="✅ SOP COMPLETE",
        border_style="green",
    ))
    sys.exit(0)
