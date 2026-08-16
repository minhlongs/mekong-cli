# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/algo_status.py — `mekong algo-status` command.

Shows algorithm health across the project:
  - Coverage summary (test files vs source files)
  - Test status per top-level project directory
  - Lines of code per project (Python + TypeScript)
  - Overall repo statistics

Usage:
    mekong algo-status [--all] [--project=src]
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

MEKONG_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _get_project_stats(project: str | None = None) -> dict:
    """Collect lines-of-code and test-file stats per project directory."""
    root = MEKONG_ROOT
    top_dirs = sorted(
        [d for d in root.iterdir() if d.is_dir() and not d.name.startswith('.')]
    )

    results = {}
    total_py_lines = 0
    total_ts_lines = 0
    total_py_files = 0
    total_ts_files = 0
    total_tests = 0

    for d in top_dirs:
        name = d.name
        if name in ('node_modules', '__pycache__', '.venv'):
            continue

        py_files = list(d.rglob('*.py'))
        ts_files = [f for f in d.rglob('*.ts') if 'node_modules' not in str(f)]
        test_files = [
            f for f in (py_files + ts_files)
            if f.name.startswith('test_') or f.name.endswith('_test.py')
            or f.name.endswith('_test.ts')
        ]

        py_lines = sum(
            len(p.open().readlines()) for p in py_files
            if '.venv' not in str(p) and '__pycache__' not in str(p)
        )
        ts_lines = sum(
            len(t.open().readlines()) for t in ts_files
        )

        total_py_lines += py_lines
        total_ts_lines += ts_lines
        total_py_files += len(py_files)
        total_ts_files += len(ts_files)
        total_tests += len(test_files)

        results[name] = {
            'py_files': len(py_files),
            'ts_files': len(ts_files),
            'py_lines': py_lines,
            'ts_lines': ts_lines,
            'total_lines': py_lines + ts_lines,
            'test_files': len(test_files),
        }

    return {
        'projects': results,
        'totals': {
            'py_files': total_py_files,
            'ts_files': total_ts_files,
            'py_lines': total_py_lines,
            'ts_lines': total_ts_lines,
            'total_lines': total_py_lines + total_ts_lines,
            'test_files': total_tests,
        },
    }


def _show_algo_stats(project: str | None = None) -> None:
    """Display algorithm health dashboard."""
    stats = _get_project_stats(project)

    # Overall summary
    totals = stats['totals']
    console.print(Panel(
        f"[bold]Total:[/bold] {totals['py_files'] + totals['ts_files']} files | "
        f"{totals['total_lines']:,} lines ({totals['py_lines']:,} py, {totals['ts_lines']:,} ts) | "
        f"{totals['test_files']} test files",
        title="📊 Mekong CLI — Algorithm Health",
        border_style="blue",
    ))

    if project:
        # Single project view
        proj = stats['projects'].get(project)
        if not proj:
            console.print(f"[red]Project '{project}' not found.[/red]")
            return
        table = Table(title=f"Project: {project}")
        table.add_column("Metric", style="bold")
        table.add_column("Value")
        table.add_row("Python files", str(proj['py_files']))
        table.add_row("TypeScript files", str(proj['ts_files']))
        table.add_row("Python lines", f"{proj['py_lines']:,}")
        table.add_row("TypeScript lines", f"{proj['ts_lines']:,}")
        table.add_row("Total lines", f"{proj['total_lines']:,}")
        table.add_row("Test files", str(proj['test_files']))
        console.print(table)
    else:
        # All projects view
        table = Table(title="Lines per Project")
        table.add_column("Project", style="bold")
        table.add_column("Py Files")
        table.add_column("TS Files")
        table.add_column("Total Lines")
        table.add_column("Tests")

        for name, data in sorted(
            stats['projects'].items(), key=lambda x: x[1]['total_lines'], reverse=True
        ):
            if data['total_lines'] == 0:
                continue
            table.add_row(
                name,
                str(data['py_files']),
                str(data['ts_files']),
                f"{data['total_lines']:,}",
                str(data['test_files']),
            )

        # Totals row
        table.add_row(
            "[bold]TOTAL[/bold]",
            str(totals['py_files']),
            str(totals['ts_files']),
            f"[bold]{totals['total_lines']:,}[/bold]",
            str(totals['test_files']),
        )
        console.print(table)


def register(cli: typer.Typer) -> None:
    """Register `mekong algo-status` command."""

    @cli.command("algo-status")
    def algo_status_cmd(
        all: bool = typer.Option(False, "--all", "-a", help="Show all projects"),
        project: str | None = typer.Option(None, "--project", "-p", help="Filter to single project"),
    ) -> None:
        """Show algorithm health — coverage, test status, lines per project."""
        _show_algo_stats(project)
