# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI Clean Command - Clean cache, temp files, build artifacts
"""

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from src.commands.clean_helpers import (
    CLEAN_TARGETS,
    find_files_to_clean,
    get_clean_patterns,
    human_readable_size,
    run_full_clean,
)

app = typer.Typer(name="clean", help="Clean cache, temp files, build artifacts")
console = Console()


@app.command()
def cache() -> None:
    """Clean LLM and vector cache"""
    _clean_target("cache", "cache files")


@app.command()
def build() -> None:
    """Clean build artifacts"""
    _clean_target("build", "build artifacts")


@app.command()
def temp() -> None:
    """Clean temporary files"""
    _clean_target("temp", "temporary files")


@app.command()
def logs() -> None:
    """Clean log files"""
    _clean_target("logs", "log files")


@app.command()
def all(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be cleaned")
) -> None:
    """Clean everything (cache, build, temp, logs)"""
    run_full_clean(dry_run=dry_run)


def _clean_target(target: str, description: str) -> None:
    """Clean a specific target category"""
    base_path = Path.cwd()
    patterns = get_clean_patterns(target)

    console.print(
        Panel(
            f"🧹 Cleaning {description}...",
            border_style="yellow",
        )
    )

    to_clean = find_files_to_clean(base_path, patterns)

    if not to_clean:
        console.print(f"[green]✓ No {description} found[/green]")
        return

    table = Table(title=f"Deleting {description} ({len(to_clean)} items)")
    table.add_column("Path", style="cyan")
    table.add_column("Size", style="dim")

    for path in to_clean:
        table.add_row(str(path.relative_to(base_path)), human_readable_size(path))

    console.print(table)

    if not Confirm.ask(f"\nDelete {len(to_clean)} {description}?", default=False):
        console.print("[dim]Cancelled[/dim]")
        return

    deleted_count = 0
    for path in to_clean:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            deleted_count += 1
        except Exception as e:
            console.print(f"[red]✗ Failed to delete {path}: {e}[/red]")

    console.print(f"\n[green]✓ Deleted {deleted_count}/{len(to_clean)} {description}[/green]")


@app.command()
def list(
    target: str = typer.Option("all", "--target", "-t", help="Target category")
) -> None:
    """List files that would be cleaned (dry run)"""
    base_path = Path.cwd()
    patterns = (
        get_clean_patterns(target) if target != "all" else get_clean_patterns("all")
    )

    console.print(
        Panel(
            f"📋 Files matching '{target}' patterns",
            border_style="blue",
        )
    )

    to_clean = find_files_to_clean(base_path, patterns)

    if not to_clean:
        console.print("[green]✓ No files found[/green]")
        return

    table = Table(title=f"Matched files ({len(to_clean)} items)")
    table.add_column("Path", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Size", style="dim")

    for path in to_clean:
        table.add_row(
            str(path.relative_to(base_path)),
            "dir" if path.is_dir() else "file",
            human_readable_size(path),
        )

    console.print(table)


def main():
    """Entry point for clean command"""
    app()


__all__ = [
    "CLEAN_TARGETS",
    "_clean_target",
    "all",
    "app",
    "build",
    "cache",
    "console",
    "find_files_to_clean",
    "get_clean_patterns",
    "human_readable_size",
    "list",
    "logs",
    "main",
    "temp",
]


if __name__ == "__main__":
    app()
