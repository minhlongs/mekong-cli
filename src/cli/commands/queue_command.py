# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/queue_command.py — Autonomous Distributed Task Queue & DLQ CLI.

Provides commands to enqueue prioritized tasks, monitor queue status, lease tasks for execution,
and manage the dead-letter queue (DLQ) for replay and fault recovery.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.task_queue import TaskPriority, get_task_queue

console = Console()
queue_app = typer.Typer(name="queue", help="📬 Autonomous Distributed Task Queue & Dead-Letter Mesh")


@queue_app.command(name="enqueue")
def queue_enqueue(
    name: str = typer.Argument(..., help="Descriptive name of the task to schedule"),
    priority: str = typer.Option(
        "normal",
        "--priority",
        "-p",
        help="Priority level: critical, high, normal, or low",
    ),
    payload: str = typer.Option(
        "{}",
        "--payload",
        help="JSON payload string passed to worker",
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-r",
        help="Maximum retry attempts on task failure",
    ),
    delay_sec: float = typer.Option(
        0.0,
        "--delay-sec",
        "-d",
        help="Delay execution by N seconds",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON task details",
    ),
) -> None:
    """Schedule a new task for prioritized execution."""
    try:
        parsed_payload = json.loads(payload) if payload else {}
    except Exception as exc:
        console.print(f"[red]Invalid JSON payload: {exc}[/red]")
        raise typer.Exit(code=1)

    tq = get_task_queue()
    task = tq.enqueue(
        name=name,
        payload=parsed_payload,
        priority=priority,
        max_retries=max_retries,
        delay_sec=delay_sec,
    )

    if json_output:
        print(json.dumps(task.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]✓ Task Enqueued Successfully[/bold green]\n"
            f"[dim]Task ID:[/dim]  {task.task_id}\n"
            f"[dim]Name:[/dim]     {task.name}\n"
            f"[dim]Priority:[/dim] [cyan]{TaskPriority(task.priority).name}[/cyan]\n"
            f"[dim]Retries:[/dim]  {task.max_retries}\n"
            f"[dim]Delay:[/dim]    {delay_sec:.1f}s",
            title="Task Queue Dispatch",
            border_style="green",
        )
    )


@queue_app.command(name="status")
def queue_status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON queue metrics",
    ),
) -> None:
    """Inspect current queue depth, active worker leases, and dead-letter count."""
    tq = get_task_queue()
    status = tq.get_status()

    if json_output:
        print(json.dumps(status, indent=2))
        return

    console.print(
        Panel(
            f"[bold cyan]Autonomous Task Queue Status[/bold cyan]\n"
            f"[dim]Total Tasks:[/dim]   {status['total_tasks']}\n"
            f"[dim]Pending:[/dim]       [yellow]{status['pending']}[/yellow]\n"
            f"[dim]Running:[/dim]       [cyan]{status['running']}[/cyan]\n"
            f"[dim]Completed:[/dim]     [green]{status['completed']}[/green]\n"
            f"[dim]Dead-Letter:[/dim]    [red]{status['dead_letter']}[/red]",
            title="Task Queue Metrics",
            border_style="cyan",
        )
    )


@queue_app.command(name="process")
def queue_process(
    worker_id: str = typer.Option(
        "",
        "--worker-id",
        "-w",
        help="Worker identifier (defaults to process PID)",
    ),
    limit: int = typer.Option(
        1,
        "--limit",
        "-l",
        help="Maximum tasks to lease for processing",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON leased tasks",
    ),
) -> None:
    """Lease eligible pending tasks for execution."""
    w_id = worker_id or f"worker_{os.getpid()}"
    tq = get_task_queue()
    tasks = tq.lease_tasks(worker_id=w_id, limit=limit)

    if json_output:
        print(json.dumps([t.to_dict() for t in tasks], indent=2))
        return

    if not tasks:
        console.print("[dim]No pending tasks available for leasing.[/dim]")
        return

    table = Table(title=f"Leased Tasks for Worker '{w_id}'", box=ROUNDED)
    table.add_column("Task ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Priority")
    table.add_column("Leased Until", style="dim")

    for t in tasks:
        prio_color = "red" if t.priority == 0 else ("yellow" if t.priority == 1 else "white")
        table.add_row(
            t.task_id,
            t.name,
            f"[{prio_color}]{TaskPriority(t.priority).name}[/{prio_color}]",
            f"{t.leased_until:.1f}" if t.leased_until else "-",
        )

    console.print(table)


@queue_app.command(name="dlq")
def queue_dlq(
    action: str = typer.Option(
        "list",
        "--action",
        "-a",
        help="DLQ action: list, retry, retry-all, or clear",
    ),
    task_id: Optional[str] = typer.Option(
        None,
        "--task-id",
        "-t",
        help="Specific task ID for retry action",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON DLQ report",
    ),
) -> None:
    """Inspect and recover failed tasks residing in the dead-letter queue."""
    tq = get_task_queue()
    act = action.lower()

    if act == "clear":
        cleared = tq.clear_dlq()
        res = {"ok": True, "action": "clear", "cleared_tasks": cleared}
        if json_output:
            print(json.dumps(res, indent=2))
        else:
            console.print(f"[green]Purged {cleared} task(s) from Dead-Letter Queue.[/green]")
        return

    if act in ("retry-all", "retry_all"):
        retried = tq.retry_all_dlq()
        res = {"ok": True, "action": "retry_all", "retried_tasks": retried}
        if json_output:
            print(json.dumps(res, indent=2))
        else:
            console.print(f"[green]Requeued {retried} task(s) for replay execution.[/green]")
        return

    if act == "retry":
        if not task_id:
            console.print("[red]Missing required --task-id for retry action.[/red]")
            raise typer.Exit(code=1)
        ok = tq.retry_dlq_task(task_id)
        res = {"ok": ok, "action": "retry", "task_id": task_id}
        if json_output:
            print(json.dumps(res, indent=2))
        else:
            if ok:
                console.print(f"[green]Task '{task_id}' requeued successfully.[/green]")
            else:
                console.print(f"[yellow]Task '{task_id}' not found in DLQ.[/yellow]")
        return

    # Default action: list DLQ tasks
    dlq_tasks = tq.get_dlq_tasks()
    if json_output:
        print(json.dumps([t.to_dict() for t in dlq_tasks], indent=2))
        return

    if not dlq_tasks:
        console.print("[dim]Dead-Letter Queue is empty. No failed tasks found.[/dim]")
        return

    table = Table(title="Dead-Letter Queue (DLQ) Tasks", box=ROUNDED)
    table.add_column("Task ID", style="red")
    table.add_column("Name", style="bold")
    table.add_column("Retries")
    table.add_column("Error Message", style="yellow")

    for t in dlq_tasks:
        table.add_row(
            t.task_id,
            t.name,
            f"{t.retry_count}/{t.max_retries}",
            t.error or "-",
        )

    console.print(table)


def register_queue_command(app: typer.Typer) -> None:
    """Register 'queue' command group onto main Typer application."""
    app.add_typer(queue_app, name="queue")
