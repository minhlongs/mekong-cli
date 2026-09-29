# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/worktree_command.py — Isolated Git Worktree Mesh CLI.

Provides command-line primitives for creating, listing, inspecting, removing,
and pruning isolated git worktrees for parallel agent swarms and branch workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.worktree_manager import (
    WorktreeManager,
    WorktreeRecord,
    get_worktree_manager,
)

console = Console()
worktree_app = typer.Typer(
    name="worktree",
    help="🌲 Git Worktree Mesh: Isolated parallel agent workspaces and branch management",
    no_args_is_help=True,
)


@worktree_app.command(name="create")
def worktree_create(
    feature: str = typer.Argument(
        ...,
        help="Feature description, ticket ID, or branch name to isolate",
    ),
    prefix: Optional[str] = typer.Option(
        None,
        "--prefix",
        "-p",
        help="Branch prefix override (feat, fix, refactor, docs, test, perf, chore)",
    ),
    base: Optional[str] = typer.Option(
        None,
        "--base",
        "-b",
        help="Base branch to branch from (defaults to main/master)",
    ),
    no_prefix: bool = typer.Option(
        False,
        "--no-prefix",
        help="Do not add branch prefix, use feature text as literal branch name",
    ),
    root: Optional[str] = typer.Option(
        None,
        "--root",
        "-r",
        help="Custom root directory to place the isolated worktree directory",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate branch and worktree path calculation without executing git mutations",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON worktree record",
    ),
) -> None:
    """Create a new isolated git worktree branching from the base branch."""
    wm = get_worktree_manager()
    try:
        record = wm.create_worktree(
            feature=feature,
            prefix=prefix,
            base_branch=base,
            no_prefix=no_prefix,
            worktree_root=root,
            dry_run=dry_run,
        )
    except Exception as exc:
        if json_output:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            console.print(f"[bold red]Failed to create worktree:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if json_output:
        res = {"ok": True, "dry_run": dry_run, "worktree": record.to_dict()}
        print(json.dumps(res, indent=2))
        return

    action_label = "[yellow][DRY RUN][/yellow] Target Worktree" if dry_run else "[bold green]✓ Created Worktree[/bold green]"
    console.print(
        Panel(
            f"{action_label}\n"
            f"[dim]Branch:[/dim]   [bold cyan]{record.branch}[/bold cyan]\n"
            f"[dim]Path:[/dim]     {record.path}\n"
            f"[dim]Commit:[/dim]   {record.commit[:10]}",
            title="Git Worktree Mesh",
            border_style="cyan" if not dry_run else "yellow",
            box=ROUNDED,
        )
    )


@worktree_app.command(name="list")
def worktree_list(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON list of worktrees",
    ),
) -> None:
    """List all registered git worktrees in the repository."""
    wm = get_worktree_manager()
    records = wm.list_worktrees()

    if json_output:
        print(json.dumps([r.to_dict() for r in records], indent=2))
        return

    if not records:
        console.print("[yellow]No git worktrees registered.[/yellow]")
        return

    table = Table(title="Git Worktree Mesh — Active Workspaces", box=ROUNDED)
    table.add_column("Type", style="bold")
    table.add_column("Branch", style="cyan")
    table.add_column("Commit", style="dim")
    table.add_column("Path")
    table.add_column("Status")

    for r in records:
        type_str = "[bold magenta]MAIN[/bold magenta]" if r.is_main else "[cyan]WORKTREE[/cyan]"
        status_parts = []
        if r.locked:
            status_parts.append(f"[red]LOCKED ({r.lock_reason or 'yes'})[/red]")
        if r.prunable:
            status_parts.append(f"[yellow]PRUNABLE ({r.prune_reason or 'yes'})[/yellow]")
        if not status_parts:
            status_parts.append("[green]ACTIVE[/green]")

        table.add_row(
            type_str,
            r.branch or "(detached)",
            r.commit[:10] if r.commit else "HEAD",
            r.path,
            ", ".join(status_parts),
        )

    console.print(table)


@worktree_app.command(name="status")
def worktree_status(
    path_or_branch: Optional[str] = typer.Argument(
        None,
        help="Optional worktree path or branch name to inspect",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON status",
    ),
) -> None:
    """Inspect status, uncommitted changes, and divergence against base branch."""
    wm = get_worktree_manager()
    stat = wm.status(path_or_branch=path_or_branch)

    if json_output:
        print(json.dumps(stat, indent=2))
        return

    if not stat.get("ok"):
        console.print(f"[bold red]Error checking status:[/bold red] {stat.get('error')}")
        raise typer.Exit(code=1)

    rec = stat["worktree"]
    dirty_color = "red" if stat.get("dirty") else "green"
    dirty_label = f"DIRTY ({stat.get('dirty_count')} uncommitted files)" if stat.get("dirty") else "CLEAN"

    console.print(
        Panel(
            f"[bold cyan]Branch:[/bold cyan]       {rec.get('branch')} "
            f"({'[magenta]MAIN[/magenta]' if rec.get('is_main') else 'WORKTREE'})\n"
            f"[dim]Path:[/dim]         {rec.get('path')}\n"
            f"[dim]Commit:[/dim]       {rec.get('commit', '')[:10]}\n"
            f"[dim]Status:[/dim]       [{dirty_color}]{dirty_label}[/{dirty_color}]\n"
            f"[dim]Divergence:[/dim]   Ahead {stat.get('ahead', 0)} / Behind {stat.get('behind', 0)} "
            f"(vs {stat.get('base_branch')})\n"
            f"[dim]Mesh Total:[/dim]   {stat.get('all_worktrees_count')} worktrees",
            title="Worktree Workspace Status",
            border_style=dirty_color,
            box=ROUNDED,
        )
    )

    if stat.get("dirty") and stat.get("dirty_files"):
        table = Table(title="Uncommitted Changes", box=ROUNDED)
        table.add_column("File", style="yellow")
        for f in stat["dirty_files"]:
            table.add_row(f)
        console.print(table)


@worktree_app.command(name="remove")
def worktree_remove(
    path_or_name: str = typer.Argument(
        ...,
        help="Worktree path, directory basename, or branch name to remove",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force removal even if untracked files or uncommitted changes exist",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON result",
    ),
) -> None:
    """Remove an isolated git worktree workspace."""
    wm = get_worktree_manager()
    try:
        success = wm.remove_worktree(path_or_name=path_or_name, force=force)
    except Exception as exc:
        if json_output:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            console.print(f"[bold red]Failed to remove worktree:[/bold red] {exc}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps({"ok": success, "target": path_or_name, "removed": True}, indent=2))
        return

    console.print(f"[bold green]✓ Successfully removed worktree:[/bold green] {path_or_name}")


@worktree_app.command(name="prune")
def worktree_prune(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate prune without deleting worktree metadata references",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON list of pruned references",
    ),
) -> None:
    """Prune stale worktree administrative tracking files."""
    wm = get_worktree_manager()
    pruned = wm.prune_worktrees(dry_run=dry_run)

    if json_output:
        print(json.dumps({"ok": True, "dry_run": dry_run, "pruned": pruned}, indent=2))
        return

    if not pruned:
        console.print("[green]No stale worktrees to prune.[/green]")
        return

    action = "Would prune" if dry_run else "Pruned"
    console.print(f"[bold green]✓ {action} {len(pruned)} stale worktree references:[/bold green]")
    for item in pruned:
        console.print(f"  • {item}")


@worktree_app.command(name="info")
def worktree_info(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON repo topology",
    ),
) -> None:
    """Display repository topology, base branch, and default worktree root."""
    wm = get_worktree_manager()
    info = wm.get_repo_info()

    if json_output:
        print(json.dumps(info, indent=2))
        return

    if not info.get("ok"):
        console.print(f"[bold red]Error reading repo topology:[/bold red] {info.get('error')}")
        raise typer.Exit(code=1)

    console.print(
        Panel(
            f"[bold cyan]Repo Path:[/bold cyan]       {info.get('repo_path')}\n"
            f"[dim]Current Branch:[/dim]  {info.get('current_branch')}\n"
            f"[dim]Base Branch:[/dim]     {info.get('base_branch')}\n"
            f"[dim]Worktree Root:[/dim]   {info.get('worktree_root')}\n"
            f"[dim]Dirty Files:[/dim]     {info.get('dirty_count')} uncommitted",
            title="Repository Topology & Worktree Config",
            border_style="cyan",
            box=ROUNDED,
        )
    )


def register_worktree_command(app: typer.Typer) -> None:
    """Register the 'worktree' command group onto the main Typer application."""
    app.add_typer(worktree_app, name="worktree")
