# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""cli/commands/eval_agent.py — `mekong eval-agent` command."""

from __future__ import annotations

import json as json_lib

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _run_eval(agent_id: str, days: int, as_json: bool) -> int:
    """Core eval logic. Returns exit code: 0=ok, 1=no data, 2=error."""
    from src.core.evals_bridge import get_evals_db_path, query_evals

    result = query_evals(agent_id=agent_id, window_days=days)
    if result.get("total_missions", 0) == 0:
        from src.core.signals.evals.offline import run_offline_eval
        from src.core.signals.local_store import _get_db_path

        legacy_res = run_offline_eval(agent_id=agent_id, window_days=days, db_path=_get_db_path())
        if legacy_res.total_missions > 0:
            if as_json:
                print(json_lib.dumps(legacy_res.summary(), indent=2))
                return 0
            rate_pct = legacy_res.success_rate * 100
            rc = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"
            table = Table(title=f"Offline Eval — agent=[bold]{agent_id}[/bold]  last {days}d (Legacy Signals)", show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
            table.add_column("Metric", style="bold", min_width=20)
            table.add_column("Value", justify="right", min_width=14)
            for k, v in [
                ("Total missions", str(legacy_res.total_missions)), ("Success rate", f"[{rc}]{rate_pct:.1f}%[/{rc}]"),
                ("p95 duration", f"{legacy_res.p95_ms:,} ms"), ("Avg credits/mission", f"{legacy_res.avg_credits:.2f}"),
                ("Window", f"{days}d"), ("DB", str(legacy_res.db_path)),
            ]:
                table.add_row(k, v)
            console.print()
            console.print(table)
            console.print()
            return 0

        if as_json:
            print(json_lib.dumps(result, indent=2))
            return 1
        console.print(f"[yellow]No missions found for agent=[bold]{agent_id}[/bold] in last {days} days.[/yellow]\n[dim]DB: {get_evals_db_path()}[/dim]\n[dim]Tip: missions are automatically recorded when executing goals or PEV plans.[/dim]")
        return 1

    if as_json:
        print(json_lib.dumps(result, indent=2))
        return 0

    rate_pct = result.get("success_rate_pct", 0.0)
    rc = "green" if rate_pct >= 90 else "yellow" if rate_pct >= 70 else "red"
    table = Table(title=f"Offline Eval — agent=[bold]{agent_id}[/bold]  last {days}d", show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column("Metric", style="bold", min_width=22)
    table.add_column("Value", justify="right", min_width=16)
    for k, v in [
        ("Total missions", str(result["total_missions"])), ("Successful missions", str(result["successful_missions"])),
        ("Failed missions", str(result["failed_missions"])), ("Success rate", f"[{rc}]{rate_pct:.1f}%[/{rc}]"),
        ("p95 duration", f"{result['p95_duration_ms']:,} ms"), ("Avg duration", f"{result['avg_duration_ms']:.1f} ms"),
        ("Avg credits/mission", f"{result['avg_credits']:.2f}"), ("Total credits", f"{result['total_credits']:.2f}"),
        ("Total tokens", f"{result['total_tokens']:,}"), ("Window", f"{days}d"), ("DB", str(result["db_path"])),
    ]:
        table.add_row(k, v)
    console.print()
    console.print(table)
    console.print()

    if clusters := result.get("failure_clusters", []):
        ct = Table(title="🔍 Diagnosed Failure Clusters", show_header=True, header_style="bold magenta")
        for col, kw in [("Cluster Category", {"style": "bold"}), ("Failures", {"justify": "right"}), ("Share", {"justify": "right"}), ("Sample Error Reason", {"style": "dim"})]:
            ct.add_column(col, **kw)
        for cl in clusters:
            sample = cl["sample_reasons"][0] if cl.get("sample_reasons") else "N/A"
            ct.add_row(cl["category"], str(cl["count"]), f"{cl['percentage']}%", sample[:47] + "..." if len(sample) > 50 else sample)
        console.print(ct)
        console.print()

    if recommendations := result.get("recommendations", []):
        console.print(Panel("\n".join(f"• {r}" for r in recommendations), title="💡 Continuous Learning Recommendations", border_style="green" if rate_pct >= 80 else "yellow"))
        console.print()

    if rate_pct < 70:
        console.print("[red bold]Warning:[/red bold] Success rate below 70% — run [bold]mekong evolve[/bold] to adapt failure-prone recipes.")
    return 0


def register(cli: typer.Typer) -> None:
    """Register `mekong eval-agent` command. Called by CLI entrypoint."""

    @cli.command("eval-agent")
    def eval_agent_cmd(
        agent_id: str = typer.Argument("all", help="Agent version slug to evaluate (e.g. v1, v2.1). 'all' = no filter."),
        days: int = typer.Option(7, "--days", "-d", help="Lookback window in days"),
        as_json: bool = typer.Option(False, "--json", help="Output JSON for scripting"),
    ) -> None:
        """Run offline eval queries on last-N-days missions from local SQLite."""
        code = _run_eval(agent_id=agent_id, days=days, as_json=as_json)
        if code != 0:
            raise typer.Exit(code=code)


__all__ = ["_run_eval", "register"]
