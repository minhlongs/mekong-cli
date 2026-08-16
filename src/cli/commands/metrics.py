# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/metrics.py — `mekong metrics` command.

Shows:
  - SQLite row count (offline evals DB)
  - Grafana URL (local, if running)
  - PostHog URL (M1 Max via CF Tunnel, when enabled)
  - Quick success-rate summary for last 7 days

Registration: export register(cli) — phase-04 calls this from entrypoint.
"""

from __future__ import annotations

import os

import typer
from rich.console import Console
from rich.table import Table

console = Console()

# URLs — override via env for custom setups
_GRAFANA_URL = os.environ.get("SIGNALS_GRAFANA_URL", "http://localhost:3000")
_POSTHOG_URL = os.environ.get(
    "SIGNALS_POSTHOG_URL", "https://posthog.m1max.cashclaw.cc"
)
_POSTHOG_ENABLED = os.environ.get("SIGNALS_POSTHOG_ENABLED", "0") == "1"


def _show_metrics(days: int = 7, agent: str = "all") -> None:
    """Core logic — separated for testability."""
    from src.core.signals.local_store import row_count, _get_db_path
    from src.core.signals.evals.offline import run_offline_eval

    db_path = _get_db_path()
    total_rows = row_count(db_path)
    result = run_offline_eval(agent_id=agent, window_days=days, db_path=db_path)

    console.print("\n[bold cyan]Mekong Signals[/bold cyan]", highlight=False)

    # URLs table
    url_table = Table(show_header=True, header_style="bold magenta", box=None)
    url_table.add_column("Service", style="bold", width=16)
    url_table.add_column("URL")
    url_table.add_column("Status", width=12)

    url_table.add_row(
        "Grafana",
        _GRAFANA_URL,
        "[yellow]on-demand[/yellow]",
    )
    posthog_status = (
        "[green]enabled[/green]"
        if _POSTHOG_ENABLED
        else "[dim]deferred[/dim]"
    )
    url_table.add_row("PostHog", _POSTHOG_URL, posthog_status)
    url_table.add_row(
        "SQLite DB",
        str(db_path),
        f"[green]{total_rows} rows[/green]" if total_rows else "[dim]empty[/dim]",
    )
    console.print(url_table)

    # Eval summary
    if result.total_missions == 0:
        console.print(
            f"\n[dim]No missions in last {days} days. "
            "Run a mission then retry.[/dim]"
        )
        return

    eval_table = Table(
        title=f"Last {days}d / agent={agent}",
        show_header=True,
        header_style="bold blue",
        box=None,
    )
    eval_table.add_column("Metric", style="bold")
    eval_table.add_column("Value", justify="right")

    rate_pct = result.success_rate * 100
    rate_color = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"
    eval_table.add_row("Total missions", str(result.total_missions))
    eval_table.add_row(
        "Success rate",
        f"[{rate_color}]{rate_pct:.1f}%[/{rate_color}]",
    )
    eval_table.add_row("p95 duration", f"{result.p95_ms:,} ms")
    eval_table.add_row("Avg credits", f"{result.avg_credits:.2f}")

    console.print(eval_table)
    console.print()


def register(cli: typer.Typer) -> None:
    """Register `mekong metrics` command. Called by phase-04 entrypoint."""

    @cli.command("metrics")
    def metrics_cmd(
        days: int = typer.Option(7, "--days", "-d", help="Lookback window in days"),
        agent: str = typer.Option("all", "--agent", "-a", help="Filter by agent_id"),
    ) -> None:
        """Show mission metrics, dashboard URLs, and offline eval summary."""
        _show_metrics(days=days, agent=agent)
