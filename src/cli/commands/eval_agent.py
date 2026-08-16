# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/eval_agent.py — `mekong eval-agent` command.

Runs offline eval queries against local signals.sqlite and prints a table.
No cloud calls — pure SQLite, works offline.

Usage:
    mekong eval-agent           # last 7d, all agents
    mekong eval-agent v1        # filter agent_id = v1
    mekong eval-agent v2.1 --days 30
    mekong eval-agent --json    # machine-readable output

Registration: export register(cli) — phase-04 calls this from entrypoint.
"""

from __future__ import annotations

import json as json_lib

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _run_eval(agent_id: str, days: int, as_json: bool) -> int:
    """
    Core eval logic. Returns exit code: 0=ok, 1=no data, 2=error.
    Separated for testability.
    """
    from src.core.signals.evals.offline import run_offline_eval
    from src.core.signals.local_store import _get_db_path

    db_path = _get_db_path()
    result = run_offline_eval(agent_id=agent_id, window_days=days, db_path=db_path)

    if as_json:
        print(json_lib.dumps(result.summary(), indent=2))
        return 0 if result.total_missions > 0 else 1

    if result.total_missions == 0:
        console.print(
            f"[yellow]No missions found for agent=[bold]{agent_id}[/bold] "
            f"in last {days} days.[/yellow]"
        )
        console.print(f"[dim]DB: {db_path}[/dim]")
        console.print(
            "[dim]Tip: emit events via emit_mission_event() at agent boundary.[/dim]"
        )
        return 1

    rate_pct = result.success_rate * 100
    rate_color = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"

    table = Table(
        title=f"Offline Eval — agent=[bold]{agent_id}[/bold]  last {days}d",
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Metric", style="bold", min_width=20)
    table.add_column("Value", justify="right", min_width=14)

    table.add_row("Total missions", str(result.total_missions))
    table.add_row(
        "Success rate",
        f"[{rate_color}]{rate_pct:.1f}%[/{rate_color}]",
    )
    table.add_row("p95 duration", f"{result.p95_ms:,} ms")
    table.add_row("Avg credits/mission", f"{result.avg_credits:.2f}")
    table.add_row("Window", f"{days}d")
    table.add_row("DB", str(result.db_path))

    console.print()
    console.print(table)
    console.print()

    # Flag if success rate is low
    if rate_pct < 70:
        console.print(
            "[red bold]Warning:[/red bold] Success rate below 70% — "
            "investigate recent mission logs."
        )

    return 0


def register(cli: typer.Typer) -> None:
    """Register `mekong eval-agent` command. Called by phase-04 entrypoint."""

    @cli.command("eval-agent")
    def eval_agent_cmd(
        agent_id: str = typer.Argument(
            "all",
            help="Agent version slug to evaluate (e.g. v1, v2.1). 'all' = no filter.",
        ),
        days: int = typer.Option(7, "--days", "-d", help="Lookback window in days"),
        as_json: bool = typer.Option(
            False, "--json", help="Output JSON for scripting"
        ),
    ) -> None:
        """Run offline eval queries on last-N-days missions from local SQLite."""
        code = _run_eval(agent_id=agent_id, days=days, as_json=as_json)
        if code != 0:
            raise typer.Exit(code=code)
