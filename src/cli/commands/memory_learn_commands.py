# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""C4 Learning Loop CLI subcommands (`mekong memory learn`)."""

from __future__ import annotations

import datetime
import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

console = Console()

_learn_app = typer.Typer(
    name="learn",
    help="Learning loop: inspect outcomes, patterns, and retry suggestions",
)


@_learn_app.command(name="record")
def learn_record_cmd(
    execution_id: str = typer.Argument(..., help="Execution / workflow ID"),
    status: str = typer.Option("success", "--status", help="success|failure|retry|partial"),
    retry_count: int = typer.Option(0, "--retries", help="Number of retries performed"),
    error: str | None = typer.Option(None, "--error", help="Error message or type"),
    provider: str | None = typer.Option(None, "--provider", help="LLM / service provider"),
    command: str | None = typer.Option(None, "--command", help="Command that was executed"),
    duration_ms: float = typer.Option(0.0, "--duration-ms", help="Wall-clock ms"),
) -> None:
    """Record an execution outcome into MemoryBridge (D1)."""
    from src.learning.outcome_recorder import ExecutionOutcome, OutcomeRecorder, OutcomeStatus

    try:
        outcome_status = OutcomeStatus(status.lower())
    except ValueError:
        console.print(f"[red]Invalid status '{status}'. Use: success|failure|retry|partial[/red]")
        raise typer.Exit(1)

    error_type, error_message = None, None
    if error:
        from src.learning.retry_hooks import _classify_error

        error_type, error_message = _classify_error(error), error

    recorder = OutcomeRecorder.get_instance()
    outcome = ExecutionOutcome(
        execution_id=execution_id, status=outcome_status, retry_count=retry_count,
        error_type=error_type, error_message=error_message, provider=provider,
        command=command, duration_ms=duration_ms,
    )
    record_id = recorder.record(outcome)
    console.print(f"[green]Recorded[/green] {execution_id} -> {status} (record={record_id[:12]})")


@_learn_app.command(name="patterns")
def learn_patterns_cmd(
    min_occurrences: int = typer.Option(3, "--min", help="Min times a pattern must repeat"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Surface recurring failure patterns (D3)."""
    from src.learning.retry_hooks import get_pattern_warnings

    patterns = get_pattern_warnings(min_occurrences=min_occurrences)
    if not patterns:
        console.print("[green]No failure patterns detected.[/green]")
        raise typer.Exit()

    if json_output:
        console.print_json(json.dumps(patterns, indent=2))
        return

    table = Table(title="Failure Patterns", border_style="red")
    table.add_column("Error Type", style="red")
    table.add_column("Provider", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Last Seen", style="dim")
    table.add_column("Suggested Action", max_width=50)
    for p in patterns:
        table.add_row(
            p["error_type"], p["provider"], str(p["occurrences"]),
            datetime.datetime.fromtimestamp(p["last_seen"]).strftime("%Y-%m-%d %H:%M"),
            p["suggested_action"],
        )
    console.print(table)


@_learn_app.command(name="similar")
def learn_similar_cmd(
    execution_id: str = typer.Argument(..., help="Execution ID to find similar outcomes for"),
    json_output: bool = typer.Option(False, "--json", help="Raw JSON output"),
) -> None:
    """Show similar past executions and their outcomes (D2)."""
    from src.learning.outcome_recorder import OutcomeRecorder

    recorder = OutcomeRecorder.get_instance()
    target = next((o for o in recorder._outcome_index if o.execution_id == execution_id), None)
    similar = recorder.find_similar_failures(
        error_type=target.error_type if target else None,
        provider=target.provider if target else None,
        command=target.command if target else None,
        limit=10,
    )
    if not similar:
        console.print(f"[yellow]No similar past executions found for '{execution_id}'.[/yellow]")
        raise typer.Exit()

    if json_output:
        console.print_json(json.dumps([o.to_dict() for o in similar], indent=2))
        return

    table = Table(title=f"Similar to {execution_id}")
    table.add_column("Execution ID", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Retries", justify="right")
    table.add_column("Error", max_width=40)
    table.add_column("Provider")
    table.add_column("Duration (ms)", justify="right")
    for o in similar:
        style = "green" if o.status.value == "success" else "red"
        table.add_row(
            o.execution_id, f"[{style}]{o.status.value}[/{style}]", str(o.retry_count),
            (o.error_message or "-")[:40], o.provider or "-", f"{o.duration_ms:.0f}",
        )
    console.print(table)


@_learn_app.command(name="stats")
def learn_stats_cmd() -> None:
    """Show learning-loop statistics (outcomes recorded, success rate, avg retries)."""
    from src.learning.outcome_recorder import OutcomeRecorder

    stats = OutcomeRecorder.get_instance().stats()
    panel_text = (
        f"[bold]Total Outcomes:[/bold] {stats['total']}\n"
        f"[bold]Success Rate:[/bold] {stats['success_rate']}%\n"
        f"[bold]Failures:[/bold] {stats['failure_count']}\n"
        f"[bold]Avg Retries:[/bold] {stats['avg_retries']}"
    )
    console.print(Panel(panel_text, title="Learning Loop Stats", border_style="cyan"))


@_learn_app.command(name="threshold")
def learn_threshold_cmd(
    error_type: str | None = typer.Option(None, "--error-type", help="Error category"),
    provider: str | None = typer.Option(None, "--provider", help="Provider name"),
    current: int = typer.Option(3, "--current", help="Current retry max_attempts"),
    max_threshold: int = typer.Option(5, "--max", help="Maximum threshold"),
) -> None:
    """Suggest auto-tuned retry threshold (D4)."""
    from src.learning.outcome_recorder import OutcomeRecorder

    suggested = OutcomeRecorder.get_instance().suggest_retry_threshold(
        error_type=error_type, provider=provider, current_threshold=current, max_threshold=max_threshold,
    )
    changed = "[yellow]raise[/yellow]" if suggested > current else ("[dim]lower[/dim]" if suggested < current else "unchanged")
    console.print(f"Suggested retry threshold: [bold]{suggested}[/bold] (current={current}, recommendation={changed})")


@_learn_app.command(name="clear")
def learn_clear_cmd(
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
) -> None:
    """Clear all recorded learning outcomes."""
    if not force:
        console.print("[red]This deletes all recorded execution outcomes from MemoryBridge.[/red]")
        if not Confirm.ask("Proceed?", default=False):
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()
    from src.learning.outcome_recorder import OutcomeRecorder, _reset_singleton

    OutcomeRecorder.get_instance().clear()
    _reset_singleton()
    console.print("[green]Learning outcomes cleared.[/green]")
