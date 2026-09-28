# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/eval_agent.py — `mekong eval-agent` command.

Runs offline eval queries against local .mekong/evals.db (with fallback to signals.sqlite).
Outputs rich summary tables, failure clusters, and recommendations.
No cloud calls — pure SQLite, works completely offline.

Usage:
    mekong eval-agent           # last 7d, all agents
    mekong eval-agent v1        # filter agent_id = v1
    mekong eval-agent v2.1 --days 30
    mekong eval-agent --json    # machine-readable output
"""

from __future__ import annotations

import json as json_lib

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _run_eval(agent_id: str, days: int, as_json: bool) -> int:
    """
    Core eval logic. Returns exit code: 0=ok, 1=no data, 2=error.
    Separated for testability.
    """
    from src.core.evals_bridge import query_evals, get_evals_db_path

    # 1. Query evals bridge (.mekong/evals.db)
    result = query_evals(agent_id=agent_id, window_days=days)

    if result.get("total_missions", 0) == 0:
        # Fallback check on legacy signals.sqlite if present
        from src.core.signals.evals.offline import run_offline_eval
        from src.core.signals.local_store import _get_db_path

        legacy_path = _get_db_path()
        legacy_res = run_offline_eval(agent_id=agent_id, window_days=days, db_path=legacy_path)
        if legacy_res.total_missions > 0:
            if as_json:
                print(json_lib.dumps(legacy_res.summary(), indent=2))
                return 0

            rate_pct = legacy_res.success_rate * 100
            rate_color = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"

            table = Table(
                title=f"Offline Eval — agent=[bold]{agent_id}[/bold]  last {days}d (Legacy Signals)",
                show_header=True,
                header_style="bold cyan",
                box=None,
                padding=(0, 2),
            )
            table.add_column("Metric", style="bold", min_width=20)
            table.add_column("Value", justify="right", min_width=14)

            table.add_row("Total missions", str(legacy_res.total_missions))
            table.add_row("Success rate", f"[{rate_color}]{rate_pct:.1f}%[/{rate_color}]")
            table.add_row("p95 duration", f"{legacy_res.p95_ms:,} ms")
            table.add_row("Avg credits/mission", f"{legacy_res.avg_credits:.2f}")
            table.add_row("Window", f"{days}d")
            table.add_row("DB", str(legacy_res.db_path))

            console.print()
            console.print(table)
            console.print()
            return 0

        # No records found in either database
        if as_json:
            print(json_lib.dumps(result, indent=2))
            return 1

        db_path = get_evals_db_path()
        console.print(
            f"[yellow]No missions found for agent=[bold]{agent_id}[/bold] "
            f"in last {days} days.[/yellow]"
        )
        console.print(f"[dim]DB: {db_path}[/dim]")
        console.print(
            "[dim]Tip: missions are automatically recorded when executing goals or PEV plans.[/dim]"
        )
        return 1

    # Format JSON output
    if as_json:
        print(json_lib.dumps(result, indent=2))
        return 0

    rate_pct = result.get("success_rate_pct", 0.0)
    rate_color = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"

    # Main Metrics Table
    table = Table(
        title=f"Offline Eval — agent=[bold]{agent_id}[/bold]  last {days}d",
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 2),
    )
    table.add_column("Metric", style="bold", min_width=22)
    table.add_column("Value", justify="right", min_width=16)

    table.add_row("Total missions", str(result["total_missions"]))
    table.add_row("Successful missions", str(result["successful_missions"]))
    table.add_row("Failed missions", str(result["failed_missions"]))
    table.add_row("Success rate", f"[{rate_color}]{rate_pct:.1f}%[/{rate_color}]")
    table.add_row("p95 duration", f"{result['p95_duration_ms']:,} ms")
    table.add_row("Avg duration", f"{result['avg_duration_ms']:.1f} ms")
    table.add_row("Avg credits/mission", f"{result['avg_credits']:.2f}")
    table.add_row("Total credits", f"{result['total_credits']:.2f}")
    table.add_row("Total tokens", f"{result['total_tokens']:,}")
    table.add_row("Window", f"{days}d")
    table.add_row("DB", str(result["db_path"]))

    console.print()
    console.print(table)
    console.print()

    # Failure Clusters Table
    clusters = result.get("failure_clusters", [])
    if clusters:
        cluster_table = Table(
            title="🔍 Diagnosed Failure Clusters",
            show_header=True,
            header_style="bold magenta",
        )
        cluster_table.add_column("Cluster Category", style="bold")
        cluster_table.add_column("Failures", justify="right")
        cluster_table.add_column("Share", justify="right")
        cluster_table.add_column("Sample Error Reason", style="dim")

        for cl in clusters:
            sample = cl["sample_reasons"][0] if cl.get("sample_reasons") else "N/A"
            if len(sample) > 50:
                sample = sample[:47] + "..."
            cluster_table.add_row(
                cl["category"],
                str(cl["count"]),
                f"{cl['percentage']}%",
                sample,
            )
        console.print(cluster_table)
        console.print()

    # Recommendations Panel
    recommendations = result.get("recommendations", [])
    if recommendations:
        rec_text = "\n".join(f"• {r}" for r in recommendations)
        console.print(Panel(
            rec_text,
            title="💡 Continuous Learning Recommendations",
            border_style="green" if rate_pct >= 80 else "yellow",
        ))
        console.print()

    # Flag if success rate is critically low
    if rate_pct < 70:
        console.print(
            "[red bold]Warning:[/red bold] Success rate below 70% — "
            "run [bold]mekong evolve[/bold] to adapt failure-prone recipes."
        )

    return 0


def register(cli: typer.Typer) -> None:
    """Register `mekong eval-agent` command. Called by CLI entrypoint."""

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


__all__ = [
    "_run_eval",
    "register",
]
